from typing import List, Optional
from app.rag.embeddings.base import EmbeddingProviderBase


class OpenAIEmbeddingProvider(EmbeddingProviderBase):
    """OpenAI text-embedding-3-small provider stub."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, dimension: int = 1536):
        self.model = model or "text-embedding-3-small"
        self.dimension = dimension

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return self.model

    async def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError("OpenAIEmbeddingProvider stub - install openai and configure OPENAI_API_KEY")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("OpenAIEmbeddingProvider stub - install openai and configure OPENAI_API_KEY")
