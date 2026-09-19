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
