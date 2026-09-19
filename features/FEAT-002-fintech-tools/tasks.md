# FEAT-002-fintech-tools: Phased Execution Plan

## Phase 1: Foundation (Data Models & Schemas)
- Define SQLAlchemy ORM models for `User`, `Account`, `Transaction`, `Payment`, `Refund`, and `Ticket`.
- Create Alembic migrations.
- Create seed data script to populate PostgreSQL with realistic test cases (e.g., successful txns, failed txns, flagged txns, different KYC states).
- Define Pydantic base schemas for standard API responses.

## Phase 2: Core Read Tools
- Implement Service Layer and Tool Handlers for:
  - `getTransaction`
  - `getAccount`
  - `getPaymentStatus`
  - `getAccountBalance`
  - `getCustomerProfile`
- Map Pydantic input models to Gemini JSON Schemas.

## Phase 3: Investigation Tools
- Implement Service Layer and Tool Handlers for:
  - `checkFraudStatus`
  - `getRefundStatus`
  - `getTransactionHistory` (with pagination support)
- Ensure tools return clean, localized errors when data is missing.

## Phase 4: Write Tools & HITL Workflows
- Implement `createSupportTicket` and `sendNotification`.
- Implement `initiateRefund`.
  - Add business logic: If `amount > 10000`, push task to Celery queue with status `pending_approval`.
- Implement `escalateToHumanAgent`.
- Map these tools and ensure idempotency keys are used where appropriate.

## Phase 5: Gemini Function Calling Integration
- Create a `ToolRegistry` class that consolidates all Pydantic schemas into a list of Gemini-compatible function definitions.
- Write the dispatcher that maps a tool call name and JSON arguments from the LLM back to the corresponding Python function.

## Phase 6: Testing
- Write Pytest unit tests for all Service Layer classes.
- Write Pytest integration tests for Tool Handlers using the PostgreSQL seed data.
- Validate LLM schema generation matches expectations.
