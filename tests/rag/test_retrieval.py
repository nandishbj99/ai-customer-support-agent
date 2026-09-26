import pytest

from app.rag.chunking import DocumentChunk
from app.rag.embeddings.mock import MockEmbeddingProvider
from app.rag.retrieval import HybridSearchEngine
from app.rag.store import VectorKnowledgeStore


@pytest.mark.asyncio
async def test_vector_knowledge_store_crud():
    store = VectorKnowledgeStore()
    provider = MockEmbeddingProvider()

    chunk1 = DocumentChunk("Refunds are processed in 3 business days.", "c1", {"doc_id": "d1", "category": "refund"})
    chunk2 = DocumentChunk("Account is frozen after multiple failed attempts.", "c2", {"doc_id": "d2", "category": "account"})

    emb1 = await provider.embed_text(chunk1.text)
    emb2 = await provider.embed_text(chunk2.text)

    store.add_chunks([chunk1, chunk2], [emb1, emb2])
    assert store.count() == 2

    # Query matching chunk 1
    query_emb = await provider.embed_text("How long for refunds?")
    results = store.search(query_emb, top_k=2)
    assert len(results) == 2
    assert results[0]["chunk_id"] in ("c1", "c2")

    # Filter by category
    filtered = store.search(query_emb, top_k=2, filter_meta={"category": "refund"})
    assert len(filtered) == 1
    assert filtered[0]["chunk_id"] == "c1"

    # Delete document d1
    deleted_count = store.delete_document("d1")
    assert deleted_count == 1
    assert store.count() == 1


@pytest.mark.asyncio
async def test_hybrid_search_rrf():
    store = VectorKnowledgeStore()
    provider = MockEmbeddingProvider()

    c1 = DocumentChunk(
        "UPI payment refund TAT is T+1 to T+3 working days per RBI guidelines.",
        "c_upi",
        {"doc_id": "d_upi", "title": "UPI TAT", "category": "refunds"},
    )
    c2 = DocumentChunk(
        "Credit card chargeback can be initiated within 60 days of transaction statement.",
        "c_card",
        {"doc_id": "d_card", "title": "Card Chargeback", "category": "disputes"},
    )
    c3 = DocumentChunk(
        "Savings account minimum balance maintenance guidelines and monthly average balance.",
        "c_savings",
        {"doc_id": "d_savings", "title": "Savings Account", "category": "account"},
    )

    embs = await provider.embed_batch([c1.text, c2.text, c3.text])
    store.add_chunks([c1, c2, c3], embs)

    engine = HybridSearchEngine(vector_store=store, embedding_provider=provider)

    # Search with keyword specific to chunk 1 ("TAT" and "UPI")
    results = await engine.search(query="UPI refund TAT", top_k=2, dense_weight=0.3)
    assert len(results) >= 1
    assert results[0]["chunk_id"] == "c_upi"
    assert "source" in results[0]
    assert results[0]["source"]["title"] == "UPI TAT"
    assert results[0]["rrf_score"] > 0
