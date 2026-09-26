import math
import pytest

from app.rag.embeddings.base import EmbeddingProviderBase
from app.rag.embeddings.factory import EmbeddingProviderFactory
from app.rag.embeddings.google import GoogleEmbeddingProvider
from app.rag.embeddings.local import LocalEmbeddingProvider
from app.rag.embeddings.mock import MockEmbeddingProvider
from app.rag.embeddings.openai import OpenAIEmbeddingProvider


@pytest.mark.asyncio
async def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimension=768)
    assert provider.get_dimension() == 768
    assert provider.get_model_name() == "mock-embedding-v1"

    vec = await provider.embed_text("What is the refund timeline?")
    assert len(vec) == 768
    # Check unit normalization: sum of squares ≈ 1.0
    norm = sum(x * x for x in vec)
    assert math.isclose(norm, 1.0, rel_tol=1e-3)

    # Batch embedding
    batch = await provider.embed_batch(["text 1", "text 2"])
    assert len(batch) == 2
    assert len(batch[0]) == 768
    assert len(batch[1]) == 768


def test_embedding_factory():
    mock_p = EmbeddingProviderFactory.create("mock")
    assert isinstance(mock_p, MockEmbeddingProvider)

    google_p = EmbeddingProviderFactory.create("google")
    assert isinstance(google_p, GoogleEmbeddingProvider)
    assert google_p.get_dimension() == 768

    with pytest.raises(ValueError, match="Unknown embedding provider 'invalid'"):
        EmbeddingProviderFactory.create("invalid")


@pytest.mark.asyncio
async def test_embedding_stubs_raise():
    openai_p = OpenAIEmbeddingProvider()
    assert openai_p.get_dimension() == 1536
    with pytest.raises(NotImplementedError, match="OpenAIEmbeddingProvider stub"):
        await openai_p.embed_text("query")

    local_p = LocalEmbeddingProvider()
    assert local_p.get_dimension() == 384
    with pytest.raises(NotImplementedError, match="LocalEmbeddingProvider stub"):
        await local_p.embed_text("query")
