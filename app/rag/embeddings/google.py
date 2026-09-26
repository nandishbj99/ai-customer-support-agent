from typing import List, Optional
import structlog
from google import genai

from app.core.config import settings
from app.rag.embeddings.base import EmbeddingProviderBase

logger = structlog.get_logger()


class GoogleEmbeddingProvider(EmbeddingProviderBase):
    """Google text embedding provider using google-genai SDK."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        client: Optional[genai.Client] = None,
        dimension: int = 768,
    ):
        self.model = model or settings.EMBED_MODEL or "text-embedding-004"
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._client = client
        self.dimension = dimension

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                self._client = genai.Client()
        return self._client

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return self.model

    async def embed_text(self, text: str) -> List[float]:
        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=text,
            )
            if response.embeddings and len(response.embeddings) > 0:
                return response.embeddings[0].values
            raise ValueError("No embeddings returned by Google API.")
        except Exception as e:
            logger.error("google_embed_text_failed", model=self.model, error=str(e))
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=texts,
            )
            if response.embeddings:
                return [e.values for e in response.embeddings]
            raise ValueError("No embeddings returned by Google API for batch.")
        except Exception as e:
            logger.error("google_embed_batch_failed", model=self.model, count=len(texts), error=str(e))
            raise
