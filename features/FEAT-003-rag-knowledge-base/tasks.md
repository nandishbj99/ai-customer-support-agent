# Execution Plan: FEAT-003-rag-knowledge-base

> **Feature ID:** `FEAT-003-rag-knowledge-base`  
> **Status:** `COMPLETED`  
> **Current Focus / Next Action:** `Integrated with Agent Orchestrator & ToolRouter; ready for HITL (FEAT-004)`  
> **Owner:** `Team`  
> **Last Updated:** 2026-09-26

---

## Phase 1: Embedding Provider Abstraction Layer
*   [x] Task 1.1: Define abstract `EmbeddingProviderBase` ABC with `embed_text()`, `embed_batch()`, `get_dimension()`, `get_model_name()`.
    - *Files:* `app/rag/embeddings/base.py`
    - *Validation:* ABC is importable, methods have `@abstractmethod` decorators
*   [x] Task 1.2: Implement `GoogleEmbeddingProvider` — default adapter using `google-genai` SDK (`text-embedding-004`).
    - *Files:* `app/rag/embeddings/google.py`
    - *Validation:* `pytest tests/rag/embeddings/test_embeddings.py`
*   [x] Task 1.3: Create provider stubs for OpenAI and local sentence-transformers (raise `NotImplementedError`).
    - *Files:* `app/rag/embeddings/openai.py`, `app/rag/embeddings/local.py`
    - *Validation:* All stubs inherit from `EmbeddingProviderBase`
*   [x] Task 1.4: Implement `EmbeddingProviderFactory` — reads `EMBED_PROVIDER` env var, returns correct adapter.
    - *Files:* `app/rag/embeddings/factory.py`
    - *Validation:* `pytest tests/rag/test_embeddings.py`

## Phase 2: Core Ingestion Pipeline
*   [x] Task 2.1: Implement recursive character chunking (target size, overlap, semantic boundary separators).
    - *Files:* `app/rag/chunking.py`
*   [x] Task 2.2: Implement `VectorKnowledgeStore` with exact cosine similarity matching.
    - *Files:* `app/rag/store.py`
*   [x] Task 2.3: Wire embedding provider into ingestion — call `EmbeddingProviderBase.embed_batch()`.
*   [x] Task 2.4: Build seed ingestion pipeline for standard fintech regulatory policies (RBI TAT, account freeze, customer liability, security).
    - *Files:* `app/rag/knowledge.py`

## Phase 3: Retrieval & Hybrid Search
*   [x] Task 3.1: Implement dense vector similarity search in `VectorKnowledgeStore`.
*   [x] Task 3.2: Integrate BM25 index (using `rank_bm25`) for sparse keyword matching.
*   [x] Task 3.3: Implement Reciprocal Rank Fusion (RRF) to combine dense vector and sparse BM25 scores.
    - *Files:* `app/rag/retrieval.py`
*   [x] Task 3.4: Formulate source attribution metadata in retrieval responses (title, category, doc_id).

## Phase 4: Refinement & Tool Integration
*   [x] Task 4.1: Integrate policy retrieval directly into `MockPolicyService` (`app/tools/mock/policy.py`).
*   [x] Task 4.2: Wire `searchPolicy` into `ToolRegistry` and `ToolServiceFactory`.
*   [x] Task 4.3: Route `searchPolicy` tool calls in `ToolRouter` to the live hybrid RAG backend.

## Phase 5: Testing & Verification
*   [x] Task 5.1: Unit tests for `EmbeddingProviderBase`, `GoogleEmbeddingProvider`, `MockEmbeddingProvider`, `EmbeddingProviderFactory`.
*   [x] Task 5.2: Unit tests for `RecursiveTextChunker` and `VectorKnowledgeStore`.
*   [x] Task 5.3: Unit tests for `HybridSearchEngine` (RRF fusion, source attribution).
*   [x] Task 5.4: Integration tests for `PolicyKnowledgeService` and `ToolRouter` delegation.

