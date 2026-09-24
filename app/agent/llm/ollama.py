from typing import Any, AsyncIterator, Dict, List, Optional

from app.agent.llm.base import LLMProviderBase
from app.agent.llm.types import LLMChunk, LLMResponse
from app.core.config import settings


class OllamaProvider(LLMProviderBase):
    """Local Ollama LLM provider stub."""

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None):
        self.model = model or "llama3.1"
        self.host = host or settings.OLLAMA_HOST

    def get_model_name(self) -> str:
        return self.model

    def get_max_tokens(self) -> int:
        return 32_768

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        raise NotImplementedError(
            "OllamaProvider is an architectural stub. Ensure Ollama is running at OLLAMA_HOST and configure client."
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
            "OllamaProvider is an architectural stub. Ensure Ollama is running at OLLAMA_HOST and configure client."
        )
        if False:
            yield
