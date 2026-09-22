# Test Strategy: FEAT-003-rag-knowledge-base

> **Feature ID:** `FEAT-003-rag-knowledge-base`  
> **Status:** `PENDING_EXECUTION`  
> **Spec Reference:** [Feature Spec](./spec.md) | [Design & ADRs](./design.md)

---

## 1. Unit Testing — Embedding Provider Abstraction

| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | `GoogleEmbeddingProvider` inherits from `EmbeddingProviderBase` | `rag.embeddings.google` | `isinstance` check passes | `PENDING` |
| `TC-02` | All provider stubs inherit from `EmbeddingProviderBase` | `rag.embeddings.*` | All stubs pass `isinstance` check | `PENDING` |
| `TC-03` | `EmbeddingProviderFactory` returns `GoogleEmbeddingProvider` for `EMBED_PROVIDER=google` | `rag.embeddings.factory` | Correct type returned | `PENDING` |
| `TC-04` | `EmbeddingProviderFactory` raises error for unknown provider | `rag.embeddings.factory` | `ValueError` raised | `PENDING` |
| `TC-05` | `GoogleEmbeddingProvider.get_dimension()` returns 768 | `rag.embeddings.google` | Returns 768 | `PENDING` |
| `TC-06` | `embed_text()` returns list of floats with correct dimension | `rag.embeddings.google` | `len(result) == 768` | `PENDING` |
| `TC-07` | `embed_batch()` processes multiple texts in one call | `rag.embeddings.google` | Returns list of N embeddings | `PENDING` |
| `TC-08` | Dimension mismatch detected on startup | `rag.embeddings.factory` | Error raised with clear message | `PENDING` |

## 2. Unit Testing — Document Processing

*   **Document Parsers:** Test PDF, Markdown, and HTML extractors with sample files to ensure text is extracted cleanly without artifacts.
*   **Chunking Logic:** Verify that the recursive chunker respects the 512 token limit and 50 token overlap.
*   **Embedding API Mock:** Mock the `EmbeddingProviderBase` (NOT the Google SDK directly) to test the ingestion pipeline without API costs.
*   **Search Algorithms:** Unit test the Reciprocal Rank Fusion (RRF) logic for combining hybrid search scores.

## 3. Integration Testing

*   **Database Interactions:** Test CRUD operations on PostgreSQL (metadata) and ChromaDB (vectors) simultaneously to ensure consistency.
*   **Ingestion Flow:** End-to-end test uploading a document, verifying it is chunked, embedded via the abstract provider interface, and stored in ChromaDB with correct metadata (including `embedding_model` and `embedding_dimension`).
*   **Retrieval Flow:** Insert known documents, issue queries via the abstract embedding interface, and assert that the expected top-K chunks are returned.
*   **Provider Swap Test:** Run ingestion with `GoogleEmbeddingProvider`, then verify that switching to a different-dimension provider raises a mismatch error.

## 4. Performance & Load Testing

*   **Latency Checks:** Use `pytest-benchmark` to measure retrieval latency, asserting it remains `< 500ms` under normal load.
*   **Concurrency:** Test the FastAPI search endpoint with multiple concurrent requests to ensure ChromaDB handles the load gracefully.
*   **Batch Embedding:** Verify that `embed_batch()` is used during ingestion for efficiency (not individual `embed_text()` calls).

## 5. Evaluation (RAG Metrics)

*   Create a golden dataset of 50 common fintech queries and expected document sources.
*   Evaluate retrieval performance using metrics like:
    *   **Hit Rate:** Does the top-5 contain the correct source?
    *   **MRR (Mean Reciprocal Rank):** How high up is the correct source in the results?
*   Verify that source attribution is always present and accurate for every returned chunk.

## 6. Embedding Provider Contract Tests

| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-09` | All providers return `list[float]` from `embed_text()` | `rag.embeddings.*` | Type check passes | `PENDING` |
| `TC-10` | `get_dimension()` matches actual embedding length | `rag.embeddings.*` | `len(embed_text(x)) == get_dimension()` | `PENDING` |
| `TC-11` | `get_model_name()` returns non-empty string | `rag.embeddings.*` | String length > 0 | `PENDING` |
| `TC-12` | Provider handles empty string input gracefully | `rag.embeddings.*` | Returns valid embedding or clear error | `PENDING` |
