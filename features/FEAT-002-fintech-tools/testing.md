# FEAT-002-fintech-tools: Test Strategy

## 1. Overview
Testing the Fintech Tool Layer ensures that the deterministic APIs behave correctly and safely, preventing the LLM from executing unauthorized or invalid operations.

## 2. Test Types

### 2.1 Unit Tests (Service Layer & Tool Handlers)
- **Scope:** Individual Pydantic validation, Service Layer logic (mocking the DB session), and Tool Handler response formatting.
- **Tools:** `pytest`, `unittest.mock`.
- **Key Scenarios:**
  - Pydantic models correctly reject invalid inputs (e.g., negative refund amounts, missing required IDs).
  - Pydantic `.model_json_schema()` correctly generates valid Gemini tool schemas.
  - Service layer business logic (e.g., `initiateRefund` correctly sets `pending_approval` for amounts > 10,000).

### 2.2 Integration Tests (Database & Fixtures)
- **Scope:** End-to-end tool execution against a real PostgreSQL test database.
- **Tools:** `pytest`, `pytest-asyncio`, `SQLAlchemy` (test engine).
- **Setup:**
  - Use a `conftest.py` to spin up an isolated DB transaction for each test, rolling back afterward.
  - Load predefined SQL fixtures representing specific edge cases:
    - User with frozen account.
    - Transaction flagged for fraud.
    - Payment with `GATEWAY_TIMEOUT`.
- **Key Scenarios:**
  - `getTransaction` retrieves accurate joined data.
  - `checkFraudStatus` returns correct boolean and score based on fixture data.
  - Rate limiting logic successfully blocks requests exceeding limits.

## 3. Test Data Strategy
- Maintain a static set of realistic JSON/SQL fixtures in `tests/fixtures/`.
- IDs should be deterministic in tests (e.g., `user_123`, `txn_456`) to allow straightforward assertions.

## 4. Security & Access Control Tests
- Verify that calling `getTransaction` with `user_id="A"` and `txn_id="B"` (where txn B belongs to user C) returns an `UNAUTHORIZED_ACCESS` error.
- Verify that `initiateRefund` cannot be bypassed by sending string manipulation or injection attacks in the `amount` field (Pydantic type safety should catch this).

## 5. Execution
- Tests must pass via `pytest tests/features/fintech_tools/` with > 90% coverage for the tool layer.
- Run automatically in CI/CD pipeline.
