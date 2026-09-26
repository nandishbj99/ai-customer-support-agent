import pytest

from app.rag.embeddings.mock import MockEmbeddingProvider
from app.rag.knowledge import PolicyKnowledgeService
from app.rag.store import VectorKnowledgeStore


@pytest.mark.asyncio
async def test_policy_knowledge_service_seeding_and_search():
    provider = MockEmbeddingProvider()
    store = VectorKnowledgeStore()
    service = PolicyKnowledgeService(vector_store=store, embedding_provider=provider)

    # Seed default policies
    chunk_count = await service.seed_default_policies()
    assert chunk_count > 0
    assert store.count() == chunk_count

    # Search for refund turnaround time
    results = await service.search_policies(query="How many days for refund?", top_k=2)
    assert len(results) >= 1
    top = results[0]
    assert "source" in top
    assert top["source"]["title"] is not None

    # Search for unauthorized transaction liability
    dispute_results = await service.search_policies(query="unauthorized debit customer liability RBI", top_k=2)
    assert len(dispute_results) >= 1
