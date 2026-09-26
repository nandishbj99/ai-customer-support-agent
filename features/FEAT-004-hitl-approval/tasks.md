# Execution Plan: Human-in-the-Loop Approval System (FEAT-004)

**Status:** `COMPLETED`
**Current Focus:** Feature verified with 27 test cases passing (142 total in test suite)

## Phase 1: Foundation & Data Layer
*   [x] 1.1 Create database schema definitions for `ApprovalRequest`, `ApprovalRule`, and `ApprovalAuditLog` tables.
*   [x] 1.2 Implement SQLAlchemy ORM models in `app/core/models.py`.
*   [x] 1.3 Seed initial `ApprovalRule` configurations based on FR-02 (refunds > ₹10,000, reversals > ₹50,000, account freeze/closure).
*   [x] 1.4 Integrate the `transitions` library to define the formal FSM in `app/hitl/state_machine.py`.

## Phase 2: Interception & Queueing
*   [x] 2.1 Implement `ApprovalRulesEngine` in `app/hitl/rules_engine.py` to evaluate tool calls against safety thresholds and customer tier.
*   [x] 2.2 Wire `ToolRouter` in `app/agent/tool_router.py` to intercept tool execution, evaluate rules, and generate an `ApprovalRequest` if required.
*   [x] 2.3 Set up queue service with priority sorting based on SLA and monetary amount in `app/hitl/service.py`.
*   [x] 2.4 Implement background SLA monitoring and escalation in `app/hitl/tasks.py`.

## Phase 3: Dashboard APIs & Processing
*   [x] 3.1 Develop FastAPI endpoints in `app/api/v1/approvals.py` for human agents (list pending, get details, approve, reject, escalate).
*   [x] 3.2 Implement WebSocket endpoint `/api/v1/approvals/ws` and `ApprovalNotificationManager` for real-time notifications to active agents.
*   [x] 3.3 Create auto-escalation API `/api/v1/approvals/auto-escalate` for expired SLA jobs (FR-05, FR-08).

## Phase 4: Resumption & Audit
*   [x] 4.1 Implement callback tool execution upon approval using `ToolRouter.execute(bypass_hitl=True)` in `ApprovalService.approve_request`.
*   [x] 4.2 Update `FINTECH_AGENT_SYSTEM_PROMPT` in `app/agent/prompts.py` to handle approval and rejection explanations gracefully.
*   [x] 4.3 Ensure comprehensive audit logging (`ApprovalAuditLog`) on every state transition (CREATED, ESCALATED, APPROVED, REJECTED, EXECUTED, FAILED).
*   [x] 4.4 End-to-end integration and unit testing (27 test cases across 5 test suites).
