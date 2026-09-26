# Test Strategy: FEAT-003-rag-knowledge-base

> **Feature ID:** `FEAT-003-rag-knowledge-base`  
> **Status:** `PENDING_EXECUTION`  
> **Spec Reference:** [Feature Spec](./spec.md) | [Design & ADRs](./design.md)

---

## 1. Unit Testing — Embedding Provider Abstraction

| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | `GoogleEmbeddingProvider` inherits from `EmbeddingProviderBase` | `rag.embeddings.google` | `isinstance` check passes | `PASSED` |
| `TC-02` | All provider stubs inherit from `EmbeddingProviderBase` | `rag.embeddings.*` | All stubs pass `isinstance` check | `PASSED` |
| `TC-03` | `EmbeddingProviderFactory` returns `GoogleEmbeddingProvider` for `EMBED_PROVIDER=google` | `rag.embeddings.factory` | Correct type returned | `PASSED` |
| `TC-04` | `EmbeddingProviderFactory` raises error for unknown provider | `rag.embeddings.factory` | `ValueError` raised | `PASSED` |
| `TC-05` | `GoogleEmbeddingProvider.get_dimension()` returns 768 | `rag.embeddings.google` | Returns 768 | `PASSED` |
| `TC-06` | `embed_text()` returns list of floats with correct dimension | `rag.embeddings.google` | `len(result) == 768` | `PASSED` |
| `TC-07` | `embed_batch()` processes multiple texts in one call | `rag.embeddings.google` | Returns list of N embeddings | `PASSED` |
| `TC-08` | Mock provider unit vector normalization | `rag.embeddings.mock` | Unit length sum of squares = 1.0 | `PASSED` |

## 2. Unit Testing — Document Processing & Retrieval

*   **Recursive Chunker:** Verified recursive splitting by section, paragraph, sentence with chunk overlap (`tests/rag/test_chunking.py`).
*   **Vector Knowledge Store:** Verified cosine similarity vector search, metadata filtering, and document deletion (`tests/rag/test_retrieval.py`).
*   **Hybrid Search & RRF:** Verified reciprocal rank fusion blending dense vector similarity and sparse BM25 scores (`tests/rag/test_retrieval.py`).
*   **Policy Knowledge Ingestion:** Verified pre-configured RBI and fintech policy seeding (`tests/rag/test_knowledge_service.py`).
*   **Tool Dispatcher:** Verified `ToolRouter` and `MockPolicyService` delegating `searchPolicy` with source attribution (`tests/rag/test_policy_tool.py`).

## 3. Embedding Provider Contract Tests

| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-09` | All providers return `list[float]` from `embed_text()` | `rag.embeddings.*` | Type check passes | `PASSED` |
| `TC-10` | `get_dimension()` matches actual embedding length | `rag.embeddings.*` | `len(embed_text(x)) == get_dimension()` | `PASSED` |
| `TC-11` | `get_model_name()` returns non-empty string | `rag.embeddings.*` | String length > 0 | `PASSED` |
| `TC-12` | Provider handles empty batch input gracefully | `rag.embeddings.*` | Returns empty list | `PASSED` |
