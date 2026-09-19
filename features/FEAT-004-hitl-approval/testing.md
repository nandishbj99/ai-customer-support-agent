# Testing Strategy: Human-in-the-Loop Approval System (FEAT-004)

## 1. Unit Testing
*   **Rules Engine:**
    *   Test condition parsing and evaluation against various mocked tool calls.
    *   Verify edge cases (e.g., exactly ₹10,000 vs ₹10,001).
*   **State Machine:**
    *   Test all valid state transitions (Pending -> Approved, Pending -> Rejected, Pending -> Escalated).
    *   Verify invalid transitions raise appropriate errors (e.g., Approved -> Rejected).
*   **AI Agent Interceptor:**
    *   Mock the rules engine and verify the agent suspends execution and returns a "waiting for approval" internal state when a rule is triggered.

## 2. Integration Testing
*   **Database Interactions:**
    *   Verify `ApprovalRequest` persistence, updates, and audit logging.
*   **Celery Queue:**
    *   Test that submitting a request correctly enqueues a Celery task.
    *   Test the SLA auto-escalation background job using time-freezing techniques (e.g., `freezegun`).
*   **API Endpoints:**
    *   Use `httpx` async client to test the approval dashboard endpoints with mock authorization roles.

## 3. End-to-End (E2E) Testing
*   **Approval Flow:**
    *   Simulate a customer requesting a large refund via the agent interface.
    *   Verify the AI agent suspends.
    *   Simulate a human agent calling the approval API.
    *   Verify the AI agent resumes and the final action is executed.
*   **Rejection Flow:**
    *   Simulate a rejected request and verify the AI agent informs the simulated customer appropriately.
*   **WebSocket Notifications:**
    *   Connect a test client and verify it receives a push event when a new high-priority approval request is generated.

## 4. Security & Load Testing
*   **Security:** Verify only authorized roles (e.g., `agent`, `manager`) can transition approval states.
*   **Load Testing:** Populate the Redis queue with 5000+ pending requests and measure API latency for the dashboard list endpoint.
