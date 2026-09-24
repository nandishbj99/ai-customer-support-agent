from typing import Any, AsyncIterator, Dict, List, Optional

from app.agent.llm.base import LLMProviderBase
from app.agent.llm.types import LLMChunk, LLMResponse
from app.core.config import settings


class OpenAIProvider(LLMProviderBase):
    """OpenAI LLM provider stub."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or "gpt-4o"
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            # We don't raise in __init__ to allow instantiation check, but will raise in generate
            pass

    def get_model_name(self) -> str:
        return self.model

    def get_max_tokens(self) -> int:
        return 128_000

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        raise NotImplementedError(
            "OpenAIProvider is an architectural stub. Install `openai` package and set OPENAI_API_KEY to activate."
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> AsyncIterator[LLMChunk]:
        raise NotImplementedError(
            "OpenAIProvider is an architectural stub. Install `openai` package and set OPENAI_API_KEY to activate."
        )
        if False:  # Generator signature satisfaction
            yield
