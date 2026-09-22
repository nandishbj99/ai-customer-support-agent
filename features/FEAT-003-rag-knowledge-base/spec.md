# Feature Specification: FEAT-003-rag-knowledge-base (RAG Knowledge Base)

## 1. Overview
The Knowledge Base (KB) serves as the foundation for Retrieval-Augmented Generation (RAG) in the AI Customer Support Agent. It ingests, processes, stores, and retrieves domain-specific documents (policies, FAQs, troubleshooting guides) to empower the AI agent with up-to-date and accurate context for resolving customer queries.

## 2. Functional Requirements
*   **FR-01: Document Ingestion Pipeline:** Support for uploading and processing multiple document formats (PDF, Markdown, HTML). The pipeline must handle text extraction, cleaning, chunking, and embedding generation.
*   **FR-02: Semantic Search with Relevance Scoring:** Given a natural language query, retrieve the top-K most semantically similar document chunks. Each retrieved chunk must include a relevance score.
*   **FR-03: Policy Document Management:** Provide CRUD (Create, Read, Update, Delete) operations for knowledge base administrators to manage documents.
*   **FR-04: Context-Aware Retrieval:** Incorporate ongoing conversation context (not just the immediate user query) to formulate better search queries and improve retrieval accuracy.
*   **FR-05: Source Attribution:** Ensure every retrieved chunk maintains a direct link back to its source document, including specific section or page details.
*   **FR-06: Auto-Refresh / Re-Index:** Automatically trigger re-indexing and updating of vector embeddings when a source document is modified or updated.
*   **FR-07: Multi-Category Search:** Support scoped searches across predefined document categories: Payment policies, Refund policies, Account policies, Fraud prevention guidelines, Regulatory compliance (RBI guidelines), Troubleshooting guides, and FAQs.
*   **FR-08: Hybrid Search:** Combine semantic (vector) search with keyword (BM25) search to handle edge cases where exact term matching (e.g., error codes, specific product names) is critical.

## 3. Non-Functional Requirements (NFRs)
*   **Performance:** End-to-end search latency (query to retrieved chunks) must be `< 500ms`.
*   **Result Limits:** The system should return the top-5 results by default.
*   **Quality Threshold:** Implementing a minimum relevance score threshold to filter out low-confidence matches.

## 4. Document Categories
The KB will manage the following distinct document categories, allowing for scoped retrieval:
*   Payment Policies
*   Refund Policies
*   Account Policies
*   Fraud Prevention Guidelines
*   Regulatory Compliance (RBI guidelines)
*   Troubleshooting Guides
*   FAQs

---

## 5. Embedding Provider Abstraction Requirements

### FR-09: Abstract Embedding Interface
- **Description:** Define an abstract base class `EmbeddingProviderBase` with `embed_text()`, `embed_batch()`, and `get_dimension()` methods.
- **Implementation:** Python `abc.ABC` with `@abstractmethod` decorators.
- **Rationale:** The ingestion pipeline and retrieval engine must be completely decoupled from any specific embedding provider.

### FR-10: Default Provider — Google text-embedding-004
- **Description:** Implement `GoogleEmbeddingProvider` as the default adapter using the `google-genai` SDK.
- **Model:** `text-embedding-004` (768 dimensions).
- **Activation:** `EMBED_PROVIDER=google` (default).

### FR-11: Provider Stubs (Future-Ready)
- **Description:** Create stub adapters for OpenAI (`text-embedding-3-small`) and local sentence-transformers with `NotImplementedError`.
- **Files:** `rag/embeddings/openai.py`, `rag/embeddings/local.py`
- **Purpose:** Ready-made extension points for alternative embedding models.

### FR-12: Embedding Provider Factory
- **Description:** A factory class that reads `EMBED_PROVIDER` env var and instantiates the correct embedding provider.
- **Supported values:** `google` (default), `openai`, `local`.
- **Dependency Injection:** Factory provides the embedding provider to the ingestion pipeline and retrieval engine.

### FR-13: Dimension Tracking
- **Description:** `get_dimension()` must return the embedding vector dimension (e.g., 768 for Google, 1536 for OpenAI). ChromaDB collection must be configured with the correct dimension at creation time.
- **Validation:** Dimension mismatch between provider and existing ChromaDB collection must raise a clear error at startup.

### FR-14: Batch Embedding Support
- **Description:** `embed_batch()` must support batching multiple text chunks in a single API call for efficient ingestion.
- **Rate Limiting:** Respect provider-specific rate limits (e.g., Google: 1500 requests/min, OpenAI: 3000 RPM).

### FR-15: Embedding Consistency Warning
- **Description:** If `EMBED_PROVIDER` is changed after initial ingestion, the system must detect the dimension/model mismatch and warn the user that re-indexing is required.
- **Implementation:** Store the embedding model name and dimension in the document metadata table.

