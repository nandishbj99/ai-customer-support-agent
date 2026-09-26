from abc import ABC, abstractmethod
from typing import List


class EmbeddingProviderBase(ABC):
    """Abstract Base Class for text embedding providers.
    
    The RAG engine and vector store interact exclusively through this interface,
    ensuring swappable embedding models without architectural coupling.
    """

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single query or text string."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of text chunks."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the vector dimensionality of this embedding model."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier string."""
        pass
