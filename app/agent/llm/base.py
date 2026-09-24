from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from app.agent.llm.types import LLMChunk, LLMResponse


class LLMProviderBase(ABC):
    """Abstract Base Class for LLM providers.
    
    The orchestrator ReAct loop interacts ONLY with this interface, ensuring the
    agent logic remains strictly provider-agnostic.
    """

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a single completion or tool call sequence synchronously."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> AsyncIterator[LLMChunk]:
        """Stream response chunks back to the orchestrator or user interface."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the active model identifier."""
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Return the maximum context window size for the model."""
        pass
