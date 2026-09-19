# Design Document: Human-in-the-Loop Approval System (FEAT-004)

## 1. Architecture Overview
The HITL system sits between the AI Agent's tool invocation logic and the actual tool execution layer. It relies on a state machine to track approval requests and uses a persistent queue to manage pending items.

## 2. Architecture Decision Records (ADRs)

### ADR-01: Approval Queue Technology
*   **Context:** The system needs a robust queue to manage thousands of pending approval requests, handle prioritization, and support SLA tracking.
*   **Options:**
    1.  *Celery + Redis Broker:* High performance, built-in task management, retries, and monitoring (Flower).
    2.  *RabbitMQ:* Enterprise-grade message broker, highly reliable, but adds operational complexity.
    3.  *PostgreSQL SKIP LOCKED:* Database-backed queue. Simplifies infrastructure but can suffer under high concurrency and complex prioritization.
*   **Decision:** **Celery + Redis**.
*   **Rationale:** We are already using Redis for caching/sessions. Celery provides the necessary async task management and callback features needed to resume the AI agent's workflow seamlessly.

### ADR-02: Approval State Machine
*   **Context:** An approval request goes through various states (Pending, Escalated, Approved, Rejected, Executed, Failed). State transitions must be strictly controlled and auditable.
*   **Options:**
    1.  *Simple ENUM status column:* Easy to implement, but transition logic gets scattered in business code.
    2.  *Formal State Machine Library (e.g., `transitions`):* Centralized rules, strict transition validation, built-in callback hooks.
*   **Decision:** **Formal FSM with `transitions` library**.
*   **Rationale:** Given the strict compliance requirements of a fintech application, a formal state machine ensures auditable state changes and prevents invalid transitions (e.g., executing a rejected request).

### ADR-03: Agent Suspension Strategy
*   **Context:** While waiting for human approval, the AI agent's execution loop must pause. How does it resume once a decision is made?
*   **Options:**
    1.  *Agent Polls Status:* AI agent periodically checks the database. Wastes resources and delays response.
    2.  *Callback Webhook:* The approval system sends an HTTP callback to the agent service.
    3.  *Celery Callback / Async Workflow:* Using Celery chords or chains to trigger a resume task.
*   **Decision:** **Celery callback (chord/chain)**.
*   **Rationale:** Since we are using Celery for the queue, chaining tasks allows the approval task to automatically trigger the agent continuation task upon completion without relying on external webhooks or inefficient polling.

### ADR-04: Threshold Configuration
*   **Context:** The rules defining what requires approval (e.g., amount > ₹10,000) may change frequently based on business needs.
*   **Options:**
    1.  *Hardcoded constants:* Requires code changes and redeployment.
    2.  *YAML config file:* Requires service restart to pick up changes.
    3.  *Database-driven rules engine:* Editable via admin panel, applies immediately.
*   **Decision:** **Database-driven rules engine**.
*   **Rationale:** Fintech compliance rules change rapidly. Allowing operations teams to update thresholds dynamically without developer intervention is critical.

## 3. Data Models
### `ApprovalRequest`
*   `id`: UUID
*   `agent_session_id`: UUID
*   `tool_name`: String
*   `tool_arguments`: JSON
*   `context`: JSON (AI reasoning, customer summary)
*   `status`: Enum (PENDING, ESCALATED, APPROVED, REJECTED)
*   `amount`: Decimal (optional, for sorting)
*   `created_at`, `updated_at`: Datetime
*   `approver_id`: UUID (nullable)
*   `rejection_reason`: String (nullable)

### `ApprovalRule`
*   `id`: UUID
*   `rule_name`: String (e.g., "High Value Refund")
*   `condition_expression`: String (e.g., `tool == 'refund' and amount > 10000`)
*   `required_role`: String (e.g., "manager")
*   `is_active`: Boolean
