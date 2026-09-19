# FEAT-002-fintech-tools: Fintech Tool Layer Specification

## 1. Overview
This feature implements the Deterministic API Layer (Fintech Tools) for the AI Customer Support Agent. The LLM never interacts with the database directly; instead, it uses Gemini's function calling feature to invoke these explicitly defined tools. This layer enforces business rules, access control, rate limiting, and structured data access to various fintech subdomains (payments, accounts, transactions, fraud, etc.).

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
