import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi

from app.rag.embeddings.base import EmbeddingProviderBase
from app.rag.store import VectorKnowledgeStore


def simple_tokenize(text: str) -> List[str]:
    """Lowercase tokenization splitting on non-alphanumeric characters."""
    return re.findall(r"\w+", text.lower())


class HybridSearchEngine:
    """Combines Dense Vector similarity and BM25 Sparse keyword search with Reciprocal Rank Fusion (RRF)."""

    def __init__(
        self,
        vector_store: VectorKnowledgeStore,
        embedding_provider: EmbeddingProviderBase,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.rrf_k = rrf_k
        self._bm25_index: Optional[BM25Okapi] = None
        self._bm25_chunk_ids: List[str] = []
        self._sync_bm25_index()

    def _sync_bm25_index(self) -> None:
        """Build or refresh BM25 inverted index from vector store chunks."""
        all_chunks = self.vector_store.get_all_chunks()
        if not all_chunks:
            self._bm25_index = None
            self._bm25_chunk_ids = []
            return

        corpus = [simple_tokenize(c["text"]) for c in all_chunks]
        self._bm25_chunk_ids = [c["chunk_id"] for c in all_chunks]
        self._bm25_index = BM25Okapi(corpus)

    def refresh_index(self) -> None:
        self._sync_bm25_index()

    async def search(
        self,
        query: str,
        top_k: int = 5,
        dense_weight: float = 0.7,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search over policy documents."""
        query = query.strip()
        if not query or self.vector_store.count() == 0:
            return []

        filter_meta = {"category": category} if category else None

        # 1. Dense Vector Search
        query_embedding = await self.embedding_provider.embed_text(query)
        dense_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,
            filter_meta=filter_meta,
        )

        # 2. Sparse BM25 Search
        sparse_scores: Dict[str, float] = {}
        if self._bm25_index is not None and self._bm25_chunk_ids:
            query_tokens = simple_tokenize(query)
            scores = self._bm25_index.get_scores(query_tokens)
            for cid, score in zip(self._bm25_chunk_ids, scores):
                if score > 0:
                    chunk_meta = self.vector_store.chunks[cid].get("metadata", {})
                    if category and chunk_meta.get("category") != category:
                        continue
                    sparse_scores[cid] = float(score)

        # Rank sparse results
        sorted_sparse = sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)[: top_k * 2]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        candidate_data: Dict[str, Dict[str, Any]] = {}

        # Add dense ranks
        for rank, res in enumerate(dense_results):
            cid = res["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (dense_weight / (self.rrf_k + rank + 1))
            candidate_data[cid] = res

        # Add sparse ranks
        sparse_weight = 1.0 - dense_weight
        for rank, (cid, _) in enumerate(sorted_sparse):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (sparse_weight / (self.rrf_k + rank + 1))
            if cid not in candidate_data:
                chunk_dict = self.vector_store.chunks[cid]
                candidate_data[cid] = {
                    "chunk_id": cid,
                    "text": chunk_dict["text"],
                    "metadata": chunk_dict.get("metadata", {}),
                    "score": 0.0,
                }

        # Sort combined results by RRF score
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        final_results = []
        for cid, rrf_score in fused:
            item = dict(candidate_data[cid])
            item["rrf_score"] = round(rrf_score, 5)
            # Add formatted source attribution
            meta = item.get("metadata", {})
            item["source"] = {
                "title": meta.get("title", "Policy Document"),
                "category": meta.get("category", "General"),
                "doc_id": meta.get("doc_id", "doc_unknown"),
            }
            final_results.append(item)

        return final_results
