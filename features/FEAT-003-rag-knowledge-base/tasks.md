# Execution Plan: FEAT-003-rag-knowledge-base

> **Feature ID:** `FEAT-003-rag-knowledge-base`  
> **Status:** `PROPOSED`  
> **Current Focus / Next Action:** `Review ADRs & Design (Embedding Provider Abstraction) with user`  
> **Owner:** `Team`  
> **Last Updated:** 2026-09-22

---

## Phase 1: Embedding Provider Abstraction Layer
*   [ ] Task 1.1: Define abstract `EmbeddingProviderBase` ABC with `embed_text()`, `embed_batch()`, `get_dimension()`, `get_model_name()`.
    - *Files:* `app/rag/embeddings/base.py`
    - *Validation:* ABC is importable, methods have `@abstractmethod` decorators
*   [ ] Task 1.2: Implement `GoogleEmbeddingProvider` — default adapter using `google-genai` SDK (`text-embedding-004`).
    - *Files:* `app/rag/embeddings/google.py`
    - *Validation:* `pytest tests/rag/embeddings/test_google.py` — mock API calls pass
*   [ ] Task 1.3: Create provider stubs for OpenAI and local sentence-transformers (raise `NotImplementedError`).
    - *Files:* `app/rag/embeddings/openai.py`, `app/rag/embeddings/local.py`
    - *Validation:* All stubs inherit from `EmbeddingProviderBase`
*   [ ] Task 1.4: Implement `EmbeddingProviderFactory` — reads `EMBED_PROVIDER` env var, returns correct adapter.
    - *Files:* `app/rag/embeddings/factory.py`
    - *Validation:* `pytest tests/rag/embeddings/test_factory.py`

## Phase 2: Core Ingestion Pipeline
*   [ ] Task 2.1: Set up document parsing libraries (PyMuPDF for PDF, beautifulsoup for HTML, markdown).
*   [ ] Task 2.2: Implement recursive character chunking (512 tokens, 50 overlap).
*   [ ] Task 2.3: Wire embedding provider into ingestion — call `EmbeddingProviderBase.embed_batch()` (NOT Google SDK directly).
*   [ ] Task 2.4: Set up ChromaDB local instance in docker-compose, configured with dimension from `provider.get_dimension()`.
*   [ ] Task 2.5: Build the unified ingestion script/API to process a document and store embeddings + metadata in ChromaDB.
*   [ ] Task 2.6: Store `embedding_model` and `embedding_dimension` in document metadata table for mismatch detection.

## Phase 3: Metadata & Management (CRUD)
*   [ ] Task 3.1: Define SQLAlchemy models for Document Metadata (Category, Title, Source URI, Hash, embedding_model, embedding_dimension).
*   [ ] Task 3.2: Create FastAPI endpoints for uploading, updating, and deleting documents.
*   [ ] Task 3.3: Implement auto-refresh logic: trigger re-indexing when a document update is detected (via hash comparison).
*   [ ] Task 3.4: Implement startup validation — detect dimension mismatch if `EMBED_PROVIDER` changed and raise error.

## Phase 4: Retrieval & Hybrid Search
*   [ ] Task 4.1: Implement basic vector similarity search endpoint using ChromaDB — query embedding via `EmbeddingProviderBase.embed_text()`.
*   [ ] Task 4.2: Integrate BM25 index (using `rank_bm25` or similar) for sparse retrieval.
*   [ ] Task 4.3: Implement Reciprocal Rank Fusion (RRF) to combine Vector and BM25 scores.
*   [ ] Task 4.4: Add context-aware query formulation (using LLM to rewrite user query based on conversation history before searching).

## Phase 5: Refinement & Integration
*   [ ] Task 5.1: Ensure source attribution metadata is correctly formatted in retrieval responses.
*   [ ] Task 5.2: Add relevance score threshold filtering.
*   [ ] Task 5.3: Integrate the retrieval API as a tool for the ReAct AI Agent.
*   [ ] Task 5.4: Performance tuning to meet < 500ms latency requirement.

## Phase 6: Testing & Verification
*   [ ] Task 6.1: Write unit tests for `EmbeddingProviderBase`, `GoogleEmbeddingProvider`, and `EmbeddingProviderFactory`.
*   [ ] Task 6.2: Write adapter contract tests — verify all embedding providers return correct dimensions.
*   [ ] Task 6.3: Write integration tests for full ingestion → retrieval pipeline.
*   [ ] Task 6.4: Validate dimension mismatch detection on provider switch.
*   [ ] Task 6.5: Run RAG evaluation metrics (Hit Rate, MRR) on golden dataset.
