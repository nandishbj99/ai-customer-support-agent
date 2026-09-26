from typing import List, Optional
from app.rag.embeddings.base import EmbeddingProviderBase


class LocalEmbeddingProvider(EmbeddingProviderBase):
    """Local sentence-transformers embedding provider stub."""

    def __init__(self, model: Optional[str] = None, dimension: int = 384):
        self.model = model or "all-MiniLM-L6-v2"
        self.dimension = dimension

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return self.model

    async def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError("LocalEmbeddingProvider stub - install sentence-transformers")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("LocalEmbeddingProvider stub - install sentence-transformers")
