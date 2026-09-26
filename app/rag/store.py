from typing import Any, Dict, List, Optional
import numpy as np

from app.rag.chunking import DocumentChunk


class VectorKnowledgeStore:
    """In-memory and persistent vector knowledge store with exact cosine similarity."""

    def __init__(self, collection_name: str = "fintech_policies"):
        self.collection_name = collection_name
        self.chunks: Dict[str, Dict[str, Any]] = {}
        self.vectors: Dict[str, np.ndarray] = {}

    def count(self) -> int:
        return len(self.chunks)

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> None:
        """Add or update document chunks with their dense embeddings."""
        for chunk, emb in zip(chunks, embeddings):
            c_dict = chunk.to_dict()
            self.chunks[chunk.chunk_id] = c_dict

            v = np.array(emb, dtype=np.float32)
            norm = np.linalg.norm(v)
            if norm > 0:
                v = v / norm
            self.vectors[chunk.chunk_id] = v

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_meta: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search top-k chunks by cosine similarity."""
        if not self.vectors:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        results = []
        for chunk_id, doc_vec in self.vectors.items():
            chunk_data = self.chunks[chunk_id]
            meta = chunk_data.get("metadata", {})

            # Apply metadata filters if provided
            if filter_meta:
                match = True
                for k, v in filter_meta.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            # Cosine similarity of normalized vectors is dot product
            similarity = float(np.dot(q_vec, doc_vec))

            results.append({
                "chunk_id": chunk_id,
                "text": chunk_data["text"],
                "metadata": meta,
                "score": similarity,
            })

        # Sort descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_document(self, doc_id: str) -> int:
        """Remove all chunks associated with a specific document ID."""
        to_delete = [
            cid for cid, c in self.chunks.items()
            if c.get("metadata", {}).get("doc_id") == doc_id
        ]
        for cid in to_delete:
            self.chunks.pop(cid, None)
            self.vectors.pop(cid, None)
        return len(to_delete)

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Return all stored chunks for building keyword / BM25 index."""
        return list(self.chunks.values())
