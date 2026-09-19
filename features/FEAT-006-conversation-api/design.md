# FEAT-006: Conversation API & Interface Design & ADRs

## 1. System Architecture
The Conversation API operates within a FastAPI backend, heavily utilizing Python's `asyncio` for high concurrency.
- **REST Layer:** Handles standard CRUD operations for sessions, history, and metadata.
- **WebSocket Layer:** Manages persistent connections using FastAPI's WebSocket support, integrating with Redis Pub/Sub for routing messages in a horizontally scaled environment.
- **Storage:** Redis caches active session contexts for fast ReAct loop access; PostgreSQL stores immutable chat history and audit logs.

## 2. Architecture Decision Records (ADRs)

### ADR-01: Communication Protocol — REST-only vs WebSocket-only vs Hybrid
**Context:** Multi-turn AI conversations require real-time feedback (typing indicators, streaming text) and standard CRUD operations (listing past chats).
- **Option 1: REST-only with Polling:** Easy to scale, but high latency for real-time streaming and inefficient for server-to-client updates.
- **Option 2: WebSocket-only:** All operations over a single socket. Complex error handling for CRUD operations and harder to integrate with standard CDNs/WAFs.
- **Option 3: Hybrid (REST + WebSocket):** REST for CRUD (sessions, history, feedback) and WebSocket strictly for real-time active conversation streaming.
- **Decision:** **Recommend Option 3 (Hybrid)**. It plays to the strengths of both protocols, ensuring RESTful caching/security for standard endpoints while maintaining low-latency bidirectional streams for active chats.

### ADR-02: Response Streaming Strategy
**Context:** LLM generation can be slow. Users need immediate visual feedback to perceive the system as responsive.
- **Option 1: Wait for full response:** High time-to-first-byte (TTFB), poor UX.
- **Option 2: Stream token-by-token:** Lowest latency, but visually jittery and can overwhelm the frontend rendering engine.
- **Option 3: Stream in semantic chunks:** Buffer tokens into complete words, sentences, or markdown blocks before sending to the client.
- **Decision:** **Recommend Option 3 (Stream in semantic chunks)**. Provides a readable, smooth UI experience without excessive network overhead or jitter.

### ADR-03: Session Storage
**Context:** The agent needs fast access to current conversation context, but compliance requires permanent retention of all support chats.
- **Option 1: Redis only:** Ephemeral. Loss of data on crash or eviction.
- **Option 2: PostgreSQL only:** Persistent, but high latency for every conversational turn and frequent writes can degrade performance.
- **Option 3: Hybrid (Redis + PostgreSQL):** Redis handles active session states (current context window, WebSocket connection mapping). A background Celery worker flushes completed turns to PostgreSQL.
- **Decision:** **Recommend Option 3 (Hybrid)**. Balances high performance for the active ReAct loop with ACID compliance and durability for audit logs.

### ADR-04: API Versioning Strategy
**Context:** The API contract may evolve over time as new features (e.g., voice) are added.
- **Option 1: URL path (`/api/v1/`)**: Highly visible, easy to route at the load balancer level.
- **Option 2: Accept header versioning:** Cleaner URLs, but harder to test in browser and cache effectively in some CDNs.
- **Option 3: Query parameter (`?version=1`)**: Often ignored by strict caching rules, looks messy.
- **Decision:** **Recommend Option 1 (URL path versioning)**. Best for simplicity, developer experience, and broad CDN compatibility.

## 3. Data Models (PostgreSQL via SQLAlchemy)
- `ConversationSession`: id, user_id, status (active/closed), created_at, updated_at
- `Message`: id, session_id, sender_type (user/agent/system), content, timestamp, metadata (JSON)
- `Attachment`: id, message_id, file_url, file_type
- `Feedback`: id, session_id, message_id, rating, comments
