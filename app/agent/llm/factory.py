from typing import Any, Dict, Optional, Type

from app.agent.llm.anthropic import AnthropicProvider
from app.agent.llm.base import LLMProviderBase
from app.agent.llm.gemini import GeminiProvider
from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.ollama import OllamaProvider
from app.agent.llm.openai import OpenAIProvider
from app.core.config import settings


class LLMProviderFactory:
    """Factory to instantiate LLM providers based on environment or explicit config."""

    _registry: Dict[str, Type[LLMProviderBase]] = {
        "gemini": GeminiProvider,
        "mock": MockLLMProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "local": OllamaProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[LLMProviderBase]) -> None:
        """Register or override an LLM provider type."""
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMProviderBase:
        """Create and return an LLM provider instance."""
        target_provider = (provider or settings.LLM_PROVIDER or "gemini").lower()

        if target_provider not in cls._registry:
            valid_providers = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(
                f"Unknown LLM provider '{target_provider}'. Supported providers: {valid_providers}"
            )

        provider_cls = cls._registry[target_provider]
        return provider_cls(**kwargs)
