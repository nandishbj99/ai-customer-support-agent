from typing import Any, Dict, Optional, Type

from app.core.config import settings
from app.rag.embeddings.base import EmbeddingProviderBase
from app.rag.embeddings.google import GoogleEmbeddingProvider
from app.rag.embeddings.local import LocalEmbeddingProvider
from app.rag.embeddings.mock import MockEmbeddingProvider
from app.rag.embeddings.openai import OpenAIEmbeddingProvider


class EmbeddingProviderFactory:
    """Factory to create embedding provider adapters."""

    _registry: Dict[str, Type[EmbeddingProviderBase]] = {
        "google": GoogleEmbeddingProvider,
        "mock": MockEmbeddingProvider,
        "openai": OpenAIEmbeddingProvider,
        "local": LocalEmbeddingProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[EmbeddingProviderBase]) -> None:
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def create(cls, provider: Optional[str] = None, **kwargs: Any) -> EmbeddingProviderBase:
        target = (provider or settings.EMBED_PROVIDER or "google").lower()
        if target not in cls._registry:
            valid = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(f"Unknown embedding provider '{target}'. Supported: {valid}")
        return cls._registry[target](**kwargs)
