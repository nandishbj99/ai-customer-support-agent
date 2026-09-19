# FEAT-002-fintech-tools: Fintech Tool Layer Specification

> **Feature ID:** `FEAT-002-fintech-tools`  
> **Status:** `PROPOSED`  
> **Created Date:** 2026-09-18  
> **Last Updated:** 2026-09-19  
> **Parent Spec:** [Master Project Spec](../../specs/main-spec.md)

---

## 1. Overview & Objective
This feature implements the Deterministic API Layer (Fintech Tools) for the AI Customer Support Agent using the **Adapter Pattern**. The LLM never interacts with the database or external APIs directly; instead, it uses Gemini's function calling feature to invoke tools through abstract interfaces.

Each tool has two swappable implementations:
- **Mock Adapter:** Queries local PostgreSQL seed data (dev/demo/testing)
- **Live Adapter:** Calls real external fintech APIs like Razorpay, banking APIs, Freshdesk, Twilio (production)

The agent and tool router are completely agnostic to which adapter is active — they always call the same interface. The active mode is controlled by a `TOOL_MODE` environment variable (`mock`, `live`, or `hybrid`).

## 2. Functional Requirements (Tools)

### FR-01: `getTransaction(txn_id, user_id, filters)`
- **Description:** Retrieve detailed information about a specific transaction.
- **Inputs:** `txn_id` (string, optional), `user_id` (string, required), `filters` (object, optional).
- **Validation:** Must provide either `txn_id` or strong `filters` (e.g., date range + amount) for a specific user.
- **Outputs:** amount, status, failure_reason, timestamp, merchant details, payment_method.
- **Error Codes:** `TXN_NOT_FOUND`, `UNAUTHORIZED_ACCESS`

### FR-02: `getAccount(user_id)`
- **Description:** Retrieve core account details.
- **Inputs:** `user_id` (string, required).
- **Outputs:** balance, status (active, frozen, closed), KYC status, account_type, linked_cards.
- **Error Codes:** `ACCT_NOT_FOUND`

### FR-03: `getPaymentStatus(payment_id)`
- **Description:** Get raw payment gateway status.
- **Inputs:** `payment_id` (string, required).
- **Outputs:** gateway_response, processing_stage, retry_count, updated_at.
- **Error Codes:** `PAYMENT_NOT_FOUND`, `GATEWAY_TIMEOUT`

### FR-04: `checkFraudStatus(txn_id, user_id)`
- **Description:** Check fraud flags for a transaction or user.
- **Inputs:** `txn_id` (string, optional), `user_id` (string, optional). At least one required.
- **Outputs:** is_flagged (boolean), risk_score (0-100), fraud_type, blocked_reason.
- **Error Codes:** `INVALID_INPUT`

### FR-05: `getRefundStatus(refund_id, txn_id)`
- **Description:** Get the processing status of a refund.
- **Inputs:** `refund_id` (string, optional), `txn_id` (string, optional). At least one required.
- **Outputs:** stage (initiated, processing, completed, failed), estimated_completion (timestamp), amount.
- **Error Codes:** `REFUND_NOT_FOUND`

### FR-06: `searchPolicy(query)`
- **Description:** RAG-powered policy/FAQ search. Delegates to FEAT-003 RAG engine.
- **Inputs:** `query` (string, required).
- **Outputs:** matching_snippets (array), confidence_score, policy_urls.

### FR-07: `createSupportTicket(user_id, category, description, priority)`
- **Description:** Create a support ticket in the helpdesk system.
- **Inputs:** `user_id` (required), `category` (required, enum), `description` (required), `priority` (optional, default: low).
- **Outputs:** ticket_id, status.

### FR-08: `getTransactionHistory(user_id, date_range, filters, limit, offset)`
- **Description:** Get a list of recent transactions with pagination.
- **Inputs:** `user_id` (required), `date_range` (object), `limit` (integer, max 50).
- **Outputs:** transactions (array of transaction objects), total_count, has_more.

### FR-09: `getAccountBalance(user_id)`
- **Description:** Quick balance check.
- **Inputs:** `user_id` (string, required).
- **Outputs:** available_balance, ledger_balance, currency.

### FR-10: `initiateRefund(txn_id, amount, reason)`
- **Description:** Initiate a refund.
- **Inputs:** `txn_id` (required), `amount` (required), `reason` (required).
- **Business Rule:** If amount > ₹10,000, routes to Human-in-the-Loop (HITL) queue instead of processing immediately.
- **Outputs:** refund_id, status (processing, pending_approval).

### FR-11: `escalateToHumanAgent(session_id, reason, context)`
- **Description:** Escalate the current conversation to a human agent.
- **Inputs:** `session_id` (required), `reason` (required), `context` (summary string).
- **Outputs:** escalation_id, queue_position, estimated_wait_time.

### FR-12: `getCustomerProfile(user_id)`
- **Description:** Get customer metadata.
- **Inputs:** `user_id` (required).
- **Outputs:** name, tier, loyalty_points, preferred_language, registered_date.

### FR-13: `sendNotification(user_id, channel, message)`
- **Description:** Send an email, SMS, or push notification.
- **Inputs:** `user_id` (required), `channel` (enum: email, sms, push), `message` (string).
- **Outputs:** notification_id, status.

## 3. Tool API Contracts

Example Schema definition for `initiateRefund` (to be translated to Gemini function calling schema):
```json
{
  "name": "initiateRefund",
  "description": "Initiate a refund for a transaction. Refunds > 10,000 INR require human approval.",
  "parameters": {
    "type": "object",
    "properties": {
      "txn_id": {
        "type": "string",
        "description": "The unique transaction ID to refund"
      },
      "amount": {
        "type": "number",
        "description": "Refund amount in INR"
      },
      "reason": {
        "type": "string",
        "description": "Reason for the refund"
      }
    },
    "required": ["txn_id", "amount", "reason"]
  }
}
```

Example Response:
```json
{
  "success": true,
  "data": {
    "refund_id": "ref_98765xyz",
    "status": "pending_approval",
    "message": "Refund amount exceeds auto-approval limit. Sent to human queue."
  },
  "error": null
}
```

## 4. Rate Limiting and Security
- All tool invocations must validate `user_id` authorization against the active session.
- Write operations (refunds, tickets) are rate-limited per user to prevent spam (e.g., max 3 tickets per hour).
- Read operations are rate-limited to 50 calls per minute per session.

---

## 5. Adapter Pattern Requirements

### FR-14: Abstract Tool Interfaces
- **Description:** Each tool MUST define an abstract base class (ABC) with the tool's method signature.
- **Implementation:** Use Python `abc.ABC` and `@abstractmethod` decorators.
- **Rationale:** Enforces interface contracts. Both mock and live adapters must implement the same methods.

### FR-15: Mock Adapters (Dev/Demo Mode)
- **Description:** Mock adapters query local PostgreSQL seed data via SQLAlchemy.
- **Scope:** All 13 tools must have mock adapter implementations.
- **Seed Data:** 15+ realistic scenarios covering payment failures, fraud flags, pending refunds, account states.
- **Activation:** `TOOL_MODE=mock` environment variable.

### FR-16: Live Adapters (Production Mode)
- **Description:** Live adapters call real external fintech APIs via `httpx.AsyncClient`.
- **Provider Mapping:**

| Tool | Live Provider |
| :--- | :--- |
| `getTransaction`, `getPaymentStatus`, `getRefundStatus`, `initiateRefund` | Razorpay API |
| `getAccount`, `getAccountBalance` | Core Banking API |
| `checkFraudStatus` | Internal Fraud Detection ML Service |
| `createSupportTicket` | Freshdesk API |
| `sendNotification` | Twilio (SMS) + AWS SES (Email) |
| `getCustomerProfile` | Core Banking API / CRM |
| `searchPolicy` | FEAT-003 RAG Engine (same in both modes) |
| `escalateToHumanAgent` | FEAT-004 HITL System (same in both modes) |

- **Activation:** `TOOL_MODE=live` environment variable.

### FR-17: Hybrid Mode
- **Description:** Mix mock and live adapters per tool. Useful for staging when some external APIs are available but not all.
- **Configuration:** Per-tool override via `TOOL_MODE_<TOOL_NAME>=live|mock` environment variables.
- **Activation:** `TOOL_MODE=hybrid` environment variable.

### FR-18: Tool Service Factory
- **Description:** A factory class that reads `TOOL_MODE` config and instantiates the correct adapter for each tool.
- **Dependency Injection:** Factory provides adapters to the Tool Router via FastAPI dependency injection.

### FR-19: Circuit Breaker & Retry (Live Mode)
- **Description:** All live adapters must implement circuit breaker and retry logic.
- **Circuit Breaker:** `pybreaker` — opens after 5 consecutive failures, resets after 60 seconds.
- **Retry:** `tenacity` — exponential backoff, max 3 retries for 5xx/timeout errors. No retry for 4xx.
- **Fallback:** When circuit is open, return `ToolResult(success=False, error={"code": "SERVICE_UNAVAILABLE"})`.

### FR-20: Response Normalization & Caching (Live Mode)
- **Description:** Each live adapter must normalize provider-specific responses into the standard `ToolResult` schema. The agent never sees Razorpay/Bank-specific JSON formats.
- **Caching:** Redis TTL cache for read-heavy tools:
  - `getAccount`: 30 second TTL
  - `getAccountBalance`: 10 second TTL
  - `getCustomerProfile`: 60 second TTL
  - Write tools: never cached

