from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from app.agent.llm.base import LLMProviderBase
from app.agent.llm.types import LLMChunk, LLMResponse, TokenUsage, ToolCall


class MockLLMProvider(LLMProviderBase):
    """Mock LLM Provider for unit testing and offline development."""

    def __init__(
        self,
        model: str = "mock-model",
        canned_responses: Optional[List[LLMResponse]] = None,
        response_handler: Optional[Callable[[List[Dict[str, Any]], Optional[List[Dict[str, Any]]]], LLMResponse]] = None,
    ):
        self.model = model
        self.canned_responses: List[LLMResponse] = list(canned_responses or [])
        self.response_handler = response_handler
        self.call_history: List[Dict[str, Any]] = []

    def get_model_name(self) -> str:
        return self.model

    def get_max_tokens(self) -> int:
        return 128_000

    def add_response(self, response: LLMResponse) -> None:
        self.canned_responses.append(response)

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        self.call_history.append({
            "messages": messages,
            "tools": tools,
            "system_instruction": system_instruction,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        })

        if self.response_handler:
            return self.response_handler(messages, tools)

        if self.canned_responses:
            return self.canned_responses.pop(0)

        # Default echo response
        last_msg = messages[-1].get("content", "") if messages else ""
        return LLMResponse(
            text=f"Mock response to: {last_msg}",
            tool_calls=[],
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
            model=self.model,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> AsyncIterator[LLMChunk]:
        resp = await self.generate(messages, tools, system_instruction, temperature, max_output_tokens)
        if resp.tool_calls:
            yield LLMChunk(delta_tool_calls=resp.tool_calls, finish_reason="tool_call")
        if resp.text:
            # Yield in two halves to test streaming
            mid = len(resp.text) // 2
            yield LLMChunk(delta_text=resp.text[:mid])
            yield LLMChunk(delta_text=resp.text[mid:], finish_reason="stop")
