# FEAT-006: Conversation API & Interface Specification

## 1. Overview
The Conversation API & Interface is the primary customer-facing interaction point for the AI Customer Support Agent. It provides REST and WebSocket endpoints for seamless, multi-turn, stateful conversations. This component is responsible for handling natural language queries, managing session state, streaming real-time responses from the AI agent, providing progress updates (typing indicators/investigation status), and handling file attachments for customer evidence.

## 2. Functional Requirements
- **FR-01: Single-turn Queries:** Provide a REST endpoint (`POST /api/v1/chat/sessions/{id}/messages`) for standard synchronous or asynchronous single-turn queries.
- **FR-02: Real-time Streaming:** Provide a WebSocket endpoint (`ws://host/api/v1/chat/sessions/{id}/stream`) for real-time streaming of AI responses, enabling progressive display of tokens or semantic chunks.
- **FR-03: Session Management:** Support creation, resumption, listing, and closure of conversation sessions. A single user can have multiple distinct sessions.
- **FR-04: Message History Retrieval:** Allow retrieval of paginated message history for any given session to restore UI state across devices.
- **FR-05: Progress Updates:** Push typing indicators and investigation progress updates (e.g., "Checking your recent transactions...") via WebSocket during complex agent workflows.
- **FR-06: File Attachments:** Support uploading and displaying file/screenshot attachments as part of customer evidence.
- **FR-07: Feedback Collection:** Enable customers to rate individual responses or the overall conversation.
- **FR-08: Multi-language Support:** Handle user input and AI output in multiple languages (English, Hindi, and regional languages) with seamless switching.
- **FR-09: Rich Formatting:** Deliver responses with rich formatting capabilities (Markdown, actionable links, structured interactive cards).
- **FR-10: Support Agent Search:** Provide endpoints for human agents (via admin dashboard) to search and filter active or archived conversations.
- **FR-11: CSAT Surveys:** Automatically trigger and record Customer Satisfaction (CSAT) surveys upon issue resolution.
- **FR-12: Conversation Export:** Enable customers to export conversation transcripts (PDF download or email delivery).

## 3. API Endpoints

### 3.1 Authentication
- `POST /api/v1/auth/login` - Authenticate customer.
- `POST /api/v1/auth/refresh` - Refresh JWT tokens.

### 3.2 Chat & Sessions (Customer Facing)
- `POST /api/v1/chat/sessions` - Create a new conversation session.
- `GET /api/v1/chat/sessions` - List active and historical sessions for the current user.
- `POST /api/v1/chat/sessions/{id}/messages` - Send a message to a session via REST.
- `GET /api/v1/chat/sessions/{id}/messages` - Retrieve message history (paginated).
- `WS /api/v1/chat/sessions/{id}/stream` - Connect via WebSocket for real-time bidirectional communication.
- `POST /api/v1/chat/sessions/{id}/feedback` - Submit feedback/rating for the session or specific message.
- `POST /api/v1/chat/sessions/{id}/attachments` - Upload evidence files.

### 3.3 Admin (Agent Facing)
- `GET /api/v1/admin/conversations` - Admin dashboard endpoint to list, filter, and search all conversations.

## 4. Non-Functional Requirements (NFRs)
- **NFR-01: Connection Stability:** WebSocket connections must handle sudden drops and support resume capabilities without message loss.
- **NFR-02: Message Ordering:** System must guarantee exact-once delivery and correct sequential ordering of messages.
- **NFR-03: Scalability:** Must support concurrent API and WebSocket connections using async frameworks (FastAPI).
- **NFR-04: Security:** All endpoints require strict authentication (JWT). File uploads must be scanned/validated. Sensitive data must be masked in transit.
