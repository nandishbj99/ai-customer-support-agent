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

---

## 5. Verification Results (Automated Test Execution)

**Date of Execution:** 2026-09-26  
**Status:** `ALL PASSED` (27 / 27 tests in `tests/hitl/`, 142 / 142 project-wide)

| Test Suite | Tests | Result | Coverage Area |
| :--- | :--- | :--- | :--- |
| `tests/hitl/test_state_machine.py` | 7 | `PASSED` | Transitions FSM (approve, reject, escalate, mark_executed, mark_failed, terminal states, callbacks) |
| `tests/hitl/test_rules_engine.py` | 8 | `PASSED` | Threshold evaluation (₹10,000 threshold, ₹100,000 executive tier, account freeze/close, reversal > ₹50,000, fraud overrides, VIP priority/SLA adjustment) |
| `tests/hitl/test_service.py` | 6 | `PASSED` | DB persistence, request queueing, priority ordering, tool execution on approval, role enforcement (403), audit logs, SLA auto-escalation |
| `tests/hitl/test_approvals_api.py` | 3 | `PASSED` | FastAPI endpoints (`GET /api/v1/approvals`, `GET /{id}`, `POST /{id}/approve`, `POST /{id}/reject`, `POST /{id}/escalate`, `POST /auto-escalate`) |
| `tests/hitl/test_tool_router_interception.py` | 3 | `PASSED` | Interception in ToolRouter, bypass flag handling, and low-threshold direct execution |
