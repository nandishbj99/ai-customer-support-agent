# Design & Architecture: FEAT-003-rag-knowledge-base

## 1. Architecture Overview
The RAG Knowledge Base comprises an ingestion pipeline for document processing and a retrieval pipeline for answering queries.
*   **Ingestion:** Documents -> Text Extraction -> Recursive Chunking -> Google text-embedding-004 -> ChromaDB + PostgreSQL (Metadata/Sources).
*   **Retrieval:** Query -> Query Expansion (Context) -> Hybrid Search (ChromaDB Vector + BM25 Keyword) -> Re-ranking -> Top-K Chunks to LLM.

## 2. Architectural Decision Records (ADRs)

### ADR-01: Vector Database Selection
**Context:** We need a scalable and efficient vector database to store document embeddings and perform nearest-neighbor searches.
**Options:**
1.  **ChromaDB:** Local, free, easy to integrate with Python/FastAPI.
2.  **Pinecone:** Managed, highly scalable, commercial.
3.  **Weaviate:** Self-hosted, powerful hybrid search, higher operational overhead.
4.  **pgvector:** Extension for PostgreSQL, simplifies architecture by keeping relational data and vectors together.
**Decision:** Recommend **ChromaDB for v1** (simple, local, free, easy to containerize) with a planned migration path to Pinecone for future scaling.
**Pros:** Extremely low setup cost, native Python bindings, runs well in Docker alongside our FastAPI backend.
**Cons:** Scaling beyond a single node is harder than managed solutions.

### ADR-02: Embedding Model Selection
**Context:** We need to generate dense vector representations of our text chunks for semantic search.
**Options:**
1.  **Google text-embedding-004:** Google's latest embedding model.
2.  **OpenAI text-embedding-3-small:** High performance, cost-effective.
3.  **sentence-transformers (local):** Free, runs locally, no API costs.
**Decision:** Recommend **Google text-embedding-004**.
**Pros:** Consistency with the existing Gemini ecosystem (our chosen LLM), excellent performance, simplifies API credential management.
**Cons:** Vendor lock-in, API latency compared to local models.

### ADR-03: Chunking Strategy
**Context:** Documents must be split into smaller, manageable chunks that fit into the LLM context window and capture discrete semantic meaning.
**Options:**
1.  **Fixed-size:** E.g., 512 tokens. Simple but often breaks semantic boundaries.
2.  **Semantic chunking:** Splits based on structural meaning (paragraphs, sections). Harder to implement universally across formats.
3.  **Recursive character splitting with overlap:** Splits iteratively by characters (newlines, spaces) trying to keep chunks under a limit, with token overlap.
**Decision:** Recommend **Recursive character splitting with 512 tokens + 50 token overlap**.
**Pros:** Balances simplicity with preserving semantic context. The overlap ensures context isn't lost at chunk boundaries.
**Cons:** May occasionally split a coherent thought if it exceeds the limit.

### ADR-04: Retrieval Strategy
**Context:** How do we find the most relevant chunks for a given user query?
**Options:**
1.  **Pure Vector Search:** Simple similarity search in ChromaDB. Struggles with exact keyword matches (e.g., error code "E-404").
2.  **Hybrid (BM25 + Vector):** Combines dense vector similarity with sparse keyword matching.
3.  **Vector + Cross-Encoder Re-ranking:** Retrieve many with vector, re-rank top N with a more accurate cross-encoder model.
**Decision:** Recommend **Hybrid search for v1**, add cross-encoder re-ranking in v2.
**Pros:** Addresses both semantic intent and specific terminology critical in fintech (e.g., specific regulatory codes or internal error strings).
**Cons:** Requires maintaining a separate BM25 index alongside ChromaDB.

---

### ADR-05: Embedding Provider Abstraction Pattern

- **Status:** `PROPOSED`
- **Date:** 2026-09-22

#### Context & Problem Statement
The RAG pipeline must not be locked into a single embedding provider. Different deployment scenarios require different embedding models:
- **Cloud (default):** Google `text-embedding-004` — best integration with Gemini ecosystem
- **Cost-sensitive:** OpenAI `text-embedding-3-small` — cheaper per token
- **Privacy/on-premise:** Local `sentence-transformers` — no API calls, data stays local
- **Migration:** Switching providers requires re-indexing all documents, so the abstraction must also track which model was used for existing embeddings

#### Options Considered
1. **Option A: Hardcoded Google embedding calls** — Google SDK calls in ingestion/retrieval code.
   - *Pros:* Simplest.
   - *Cons:* Provider lock-in. No seam for local model testing.
2. **Option B: Abstract `EmbeddingProviderBase` interface** — ABC with `embed_text()`, `embed_batch()`, `get_dimension()`. Factory selects via `EMBED_PROVIDER` env var.
   - *Pros:* Provider-agnostic. Consistent with FEAT-001 (LLM) and FEAT-002 (Tools) adapter patterns.
   - *Cons:* ~60 lines of abstraction. Must handle dimension mismatches on provider switch.
3. **Option C: LangChain Embeddings abstraction** — Use LangChain's `Embeddings` base class.
   - *Pros:* Pre-built adapters.
   - *Cons:* Heavy dependency, overkill for 2-3 providers.

#### Decision Outcome & Justification
**Chosen Option:** `Option B — Abstract EmbeddingProviderBase`
**Rationale:** Consistent adapter pattern across the entire project (tools, LLM, embeddings). Lightweight, fully controlled, and handles the critical dimension-mismatch scenario.

#### Implementation Details

```python
# rag/embeddings/base.py
from abc import ABC, abstractmethod

class EmbeddingProviderBase(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> list[float]: ...
    
    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    
    @abstractmethod
    def get_dimension(self) -> int: ...
    
    @abstractmethod
    def get_model_name(self) -> str: ...

# rag/embeddings/google.py — Default
class GoogleEmbeddingProvider(EmbeddingProviderBase):
    def __init__(self, model: str = "text-embedding-004", api_key: str = None):
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    async def embed_text(self, text: str) -> list[float]:
        result = await self.client.aio.models.embed_content(
            model=self.model, contents=text
        )
        return result.embeddings[0].values
    
    def get_dimension(self) -> int:
        return 768  # text-embedding-004 dimension

# rag/embeddings/factory.py
class EmbeddingProviderFactory:
    @staticmethod
    def create(provider: str = "google", **kwargs) -> EmbeddingProviderBase:
        providers = {
            "google": GoogleEmbeddingProvider,
            "openai": OpenAIEmbeddingProvider,
            "local": LocalEmbeddingProvider,
        }
        return providers[provider](**kwargs)
```

#### Dimension Mismatch Safety

| Provider | Model | Dimension | Notes |
| :--- | :--- | :--- | :--- |
| Google | text-embedding-004 | 768 | Default |
| OpenAI | text-embedding-3-small | 1536 | Higher dimension |
| Local | all-MiniLM-L6-v2 | 384 | Smallest, fastest |

> Switching providers after initial indexing requires **full re-indexing** because dimensions differ. The system stores `embedding_model` and `embedding_dimension` in the document metadata table and raises an error at startup if there's a mismatch.

#### Consequences & Impact
- **Positive:** Provider-agnostic RAG pipeline. Can use local models for privacy or testing.
- **Positive:** Batch embedding support for efficient ingestion.
- **Negative:** Must handle re-indexing on provider switch.
- **Mitigation:** Clear error messages and admin API endpoint to trigger re-indexing.

