# Test Strategy: FEAT-003-rag-knowledge-base

## 1. Unit Testing
*   **Document Parsers:** Test PDF, Markdown, and HTML extractors with sample files to ensure text is extracted cleanly without artifacts.
*   **Chunking Logic:** Verify that the recursive chunker respects the 512 token limit and 50 token overlap.
*   **Embedding API Mock:** Mock the Google GenAI embedding endpoint to test the ingestion pipeline without incurring API costs.
*   **Search Algorithms:** Unit test the Reciprocal Rank Fusion (RRF) logic for combining hybrid search scores.

## 2. Integration Testing
*   **Database Interactions:** Test CRUD operations on PostgreSQL (metadata) and ChromaDB (vectors) simultaneously to ensure consistency.
*   **Ingestion Flow:** End-to-end test uploading a document, verifying it is chunked, embedded, and stored in ChromaDB with correct metadata.
*   **Retrieval Flow:** Insert known documents, issue queries, and assert that the expected top-K chunks are returned.

## 3. Performance & Load Testing
*   **Latency Checks:** Use `pytest-benchmark` or custom scripts to measure retrieval latency, asserting it remains `< 500ms` under normal load.
*   **Concurrency:** Test the FastAPI search endpoint with multiple concurrent requests to ensure ChromaDB handles the load gracefully.

## 4. Evaluation (RAG Metrics)
*   Create a golden dataset of 50 common fintech queries and expected document sources.
*   Evaluate retrieval performance using metrics like:
    *   **Hit Rate:** Does the top-5 contain the correct source?
    *   **MRR (Mean Reciprocal Rank):** How high up is the correct source in the results?
*   Verify that source attribution is always present and accurate for every returned chunk.
