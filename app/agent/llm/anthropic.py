from typing import Any, AsyncIterator, Dict, List, Optional

from app.agent.llm.base import LLMProviderBase
from app.agent.llm.types import LLMChunk, LLMResponse
from app.core.config import settings


class AnthropicProvider(LLMProviderBase):
    """Anthropic Claude LLM provider stub."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or "claude-3-5-sonnet-20241022"
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

    def get_model_name(self) -> str:
        return self.model

    def get_max_tokens(self) -> int:
        return 200_000

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        raise NotImplementedError(
            "AnthropicProvider is an architectural stub. Install `anthropic` package and set ANTHROPIC_API_KEY to activate."
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
            "AnthropicProvider is an architectural stub. Install `anthropic` package and set ANTHROPIC_API_KEY to activate."
        )
        if False:
            yield
