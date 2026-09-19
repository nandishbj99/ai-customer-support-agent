# Execution Plan: Human-in-the-Loop Approval System (FEAT-004)

## Phase 1: Foundation & Data Layer
*   [ ] 1.1 Create database migrations for `ApprovalRequest` and `ApprovalRule` tables.
*   [ ] 1.2 Implement SQLAlchemy ORM models.
*   [ ] 1.3 Seed initial `ApprovalRule` configurations based on FR-02.
*   [ ] 1.4 Integrate the `transitions` library to define the state machine for `ApprovalRequest`.

## Phase 2: Interception & Queueing
*   [ ] 2.1 Implement the Rules Engine service to evaluate tool calls against database rules.
*   [ ] 2.2 Modify the AI Agent's ReAct loop to intercept tool execution, evaluate rules, and generate an `ApprovalRequest` if required.
*   [ ] 2.3 Set up the Celery worker for the approval queue.
*   [ ] 2.4 Implement logic to enqueue the request into Celery with priority sorting based on SLA and monetary amount.

## Phase 3: Dashboard APIs & Processing
*   [ ] 3.1 Develop FastAPI endpoints for human agents (list pending, get details, approve, reject).
*   [ ] 3.2 Implement WebSocket endpoint for real-time notifications of new requests to active agents.
*   [ ] 3.3 Create Celery background task for SLA monitoring and auto-escalation (FR-05, FR-08).

## Phase 4: Resumption & Audit
*   [ ] 4.1 Implement the Celery callback mechanism to resume the AI agent's conversation upon approval or rejection.
*   [ ] 4.2 Update the agent prompt/logic to handle rejection workflows gracefully (explaining to the user based on the rejection reason).
*   [ ] 4.3 Ensure comprehensive audit logging is written to a secure append-only log or database table upon any state transition.
*   [ ] 4.4 End-to-end integration testing.
