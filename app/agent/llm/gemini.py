import uuid
from typing import Any, AsyncIterator, Dict, List, Optional
import structlog
from google import genai
from google.genai import types

from app.agent.llm.base import LLMProviderBase
from app.agent.llm.types import LLMChunk, LLMResponse, TokenUsage, ToolCall
from app.core.config import settings

logger = structlog.get_logger()


class GeminiProvider(LLMProviderBase):
    """Google Gemini LLM provider implementation using google-genai SDK."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        client: Optional[genai.Client] = None,
    ):
        self.model = model or settings.LLM_MODEL or "gemini-2.5-flash"
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._client = client

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                self._client = genai.Client()
        return self._client

    def get_model_name(self) -> str:
        return self.model

    def get_max_tokens(self) -> int:
        return 1_048_576

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[types.Content]:
        """Convert standard message dicts into google.genai types.Content objects."""
        contents: List[types.Content] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            parts: List[types.Part] = []

            if role in ("user", "human"):
                if content:
                    parts.append(types.Part.from_text(text=str(content)))
                contents.append(types.Content(role="user", parts=parts))

            elif role in ("assistant", "model"):
                if content:
                    parts.append(types.Part.from_text(text=str(content)))
                if tool_calls:
                    for tc in tool_calls:
                        tc_name = tc.get("name") if isinstance(tc, dict) else tc.name
                        tc_args = tc.get("arguments", {}) if isinstance(tc, dict) else tc.arguments
                        parts.append(types.Part.from_function_call(name=tc_name, args=tc_args))
                contents.append(types.Content(role="model", parts=parts))

            elif role in ("tool", "function"):
                name = msg.get("name", "tool_result")
                res = content if isinstance(content, dict) else {"result": str(content)}
                parts.append(types.Part.from_function_response(name=name, response=res))
                contents.append(types.Content(role="user", parts=parts))

        return contents

    def _convert_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[types.Tool]]:
        """Wrap tool declarations in google.genai types.Tool."""
        if not tools:
            return None
        return [types.Tool(function_declarations=tools)]

    def _normalize_response(self, response: types.GenerateContentResponse) -> LLMResponse:
        """Map Gemini GenerateContentResponse into canonical LLMResponse."""
        extracted_text: Optional[str] = response.text if response.text else None
        tool_calls: List[ToolCall] = []

        if response.function_calls:
            for fc in response.function_calls:
                call_id = getattr(fc, "id", None) or f"call_{uuid.uuid4().hex[:12]}"
                tool_calls.append(
                    ToolCall(
                        id=call_id,
                        name=fc.name,
                        arguments=fc.args or {},
                    )
                )

        finish_reason = "stop"
        if tool_calls:
            finish_reason = "tool_call"
        elif response.candidates and response.candidates[0].finish_reason:
            raw_reason = str(response.candidates[0].finish_reason).lower()
            if "stop" in raw_reason:
                finish_reason = "stop"
            elif "max" in raw_reason or "length" in raw_reason:
                finish_reason = "length"
            elif "safety" in raw_reason or "block" in raw_reason:
                finish_reason = "safety"

        usage = TokenUsage()
        if response.usage_metadata:
            meta = response.usage_metadata
            usage = TokenUsage(
                prompt_tokens=getattr(meta, "prompt_token_count", 0) or 0,
                completion_tokens=getattr(meta, "candidates_token_count", 0) or 0,
                total_tokens=getattr(meta, "total_token_count", 0) or 0,
            )

        return LLMResponse(
            text=extracted_text,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            model=self.model,
        )

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        contents = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            tools=gemini_tools,
            max_output_tokens=max_output_tokens,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            return self._normalize_response(response)
        except Exception as e:
            logger.error("gemini_generation_failed", error=str(e), model=self.model)
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> AsyncIterator[LLMChunk]:
        contents = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            tools=gemini_tools,
            max_output_tokens=max_output_tokens,
        )

        try:
            response_stream = await self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            )
            async for chunk in response_stream:
                chunk_tool_calls: List[ToolCall] = []
                if chunk.function_calls:
                    for fc in chunk.function_calls:
                        call_id = getattr(fc, "id", None) or f"call_{uuid.uuid4().hex[:12]}"
                        chunk_tool_calls.append(
                            ToolCall(
                                id=call_id,
                                name=fc.name,
                                arguments=fc.args or {},
                            )
                        )

                yield LLMChunk(
                    delta_text=chunk.text,
                    delta_tool_calls=chunk_tool_calls,
                    finish_reason=str(chunk.candidates[0].finish_reason).lower()
                    if chunk.candidates and chunk.candidates[0].finish_reason
                    else None,
                )
        except Exception as e:
            logger.error("gemini_stream_failed", error=str(e), model=self.model)
            raise
