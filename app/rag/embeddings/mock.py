import hashlib
import math
from typing import List

from app.rag.embeddings.base import EmbeddingProviderBase


class MockEmbeddingProvider(EmbeddingProviderBase):
    """Deterministic Mock Embedding Provider for offline testing."""

    def __init__(self, dimension: int = 768, model: str = "mock-embedding-v1"):
        self.dimension = dimension
        self.model = model

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return self.model

    def _generate_vector(self, text: str) -> List[float]:
        """Generate a deterministic unit-normalized vector based on text sha256 hash."""
        vec = []
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        for i in range(self.dimension):
            byte_val = seed[i % len(seed)]
            # Map byte (0-255) to float (-1.0 to 1.0)
            val = (byte_val / 127.5) - 1.0 + (i * 0.001)
            vec.append(val)

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]
