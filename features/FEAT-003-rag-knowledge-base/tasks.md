# Execution Plan: FEAT-003-rag-knowledge-base

## Phase 1: Core Ingestion Pipeline
*   [ ] Task 1.1: Set up document parsing libraries (PyMuPDF for PDF, beautifulsoup for HTML, markdown).
*   [ ] Task 1.2: Implement recursive character chunking (512 tokens, 50 overlap).
*   [ ] Task 1.3: Integrate `google-genai` for `text-embedding-004`.
*   [ ] Task 1.4: Set up ChromaDB local instance in docker-compose.
*   [ ] Task 1.5: Build the unified ingestion script/API to process a document and store embeddings + metadata in ChromaDB.

## Phase 2: Metadata & Management (CRUD)
*   [ ] Task 2.1: Define SQLAlchemy models for Document Metadata (Category, Title, Source URI, Hash).
*   [ ] Task 2.2: Create FastAPI endpoints for uploading, updating, and deleting documents.
*   [ ] Task 2.3: Implement auto-refresh logic: trigger re-indexing when a document update is detected (via hash comparison).

## Phase 3: Retrieval & Hybrid Search
*   [ ] Task 3.1: Implement basic vector similarity search endpoint using ChromaDB.
*   [ ] Task 3.2: Integrate BM25 index (using `rank_bm25` or similar) for sparse retrieval.
*   [ ] Task 3.3: Implement Reciprocal Rank Fusion (RRF) to combine Vector and BM25 scores.
*   [ ] Task 3.4: Add context-aware query formulation (using LLM to rewrite user query based on conversation history before searching).

## Phase 4: Refinement & Integration
*   [ ] Task 4.1: Ensure source attribution metadata is correctly formatted in retrieval responses.
*   [ ] Task 4.2: Add relevance score threshold filtering.
*   [ ] Task 4.3: Integrate the retrieval API as a tool for the ReAct AI Agent.
*   [ ] Task 4.4: Performance tuning to meet < 500ms latency requirement.
