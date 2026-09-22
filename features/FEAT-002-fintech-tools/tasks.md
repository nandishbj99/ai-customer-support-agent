# Feature Tasks & Execution Plan: FEAT-002 — Fintech Tool Layer

> **Feature ID:** `FEAT-002-fintech-tools`  
> **Status:** `IN_PROGRESS`  
> **Current Focus / Next Action:** `Phase 4: Mock Write Tools (TASK-11 to TASK-13)`  
> **Owner:** `Team`  
> **Last Updated:** 2026-09-22

---

## 1. Quick Status Dashboard

| Metric | Value |
| :--- | :--- |
| **Current Phase** | `Phase 4: Write Tools` |
| **Tasks Completed** | 10 / 22 (45%) |
| **Blockers** | None |
| **Ready for Next Phase?** | Yes (Phase 3 Complete) |

---

## 2. Immediate Actions Needed
- [x] Action 1: Complete and review ADRs in [design.md](./design.md), especially ADR-05 (Adapter Pattern).
- [x] Action 2: Get user alignment on mock vs live adapter strategy.
- [x] Action 3: Complete Phase 1 task execution (TASK-01 to TASK-05).
- [x] Action 4: Implement Phase 2 Mock Adapters (TASK-06 to TASK-08).
- [x] Action 5: Implement Phase 3 Investigation Tools (TASK-09 to TASK-10).
- [ ] Action 6: Implement Phase 4 Mock Write Tools (TASK-11 to TASK-13).

---

## 3. Phased Task Breakdown

### Phase 1: Foundation — Data Models, Schemas & Abstract Interfaces
- [x] **TASK-01:** Define SQLAlchemy ORM models for `User`, `Account`, `Transaction`, `Payment`, `Refund`, `SupportTicket`
  - *Files:* `app/core/models.py`
  - *Validation:* `tests/test_models.py` passes
- [x] **TASK-02:** Create Alembic migrations for all tables
  - *Files:* `migrations/versions/001_initial_schema.py`
  - *Validation:* Migration file created with forward and rollback definitions
- [x] **TASK-03:** Create seed data script with 15+ realistic scenarios
  - *Files:* `app/seeds/seed_data.py`
  - *Validation:* `tests/test_seeds.py` populates all tables and verifies scenarios S-01 to S-15
- [x] **TASK-04:** Define Pydantic models for all tool inputs/outputs and the `ToolResult` wrapper
  - *Files:* `app/tools/schemas.py`
  - *Validation:* `tests/test_schemas.py` passes (TC-01, TC-02, TC-03, TC-04)
- [x] **TASK-05:** Define abstract base classes (ABCs) for all 7 core tool interfaces
  - *Files:* `app/tools/base.py` (TransactionServiceBase, AccountServiceBase, PaymentServiceBase, FraudServiceBase, RefundServiceBase, TicketServiceBase, NotificationServiceBase, EscalationServiceBase)
  - *Validation:* `tests/test_base_interfaces.py` passes

### Phase 2: Mock Adapters — Core Read Tools
- [x] **TASK-06:** Implement `MockTransactionService` (getTransaction, getTransactionHistory)
  - *Files:* `app/tools/mock/transaction.py`
  - *Validation:* `pytest tests/tools/mock/test_transaction.py` (TC-05, TC-06, TC-20, TC-23)
- [x] **TASK-07:** Implement `MockAccountService` (getAccount, getAccountBalance, getCustomerProfile)
  - *Files:* `app/tools/mock/account.py`
  - *Validation:* `pytest tests/tools/mock/test_account.py` (TC-10)
- [x] **TASK-08:** Implement `MockPaymentService` (getPaymentStatus)
  - *Files:* `app/tools/mock/payment.py`
  - *Validation:* `pytest tests/tools/mock/test_payment.py`

### Phase 3: Mock Adapters — Investigation Tools
- [x] **TASK-09:** Implement `MockFraudService` (checkFraudStatus)
  - *Files:* `app/tools/mock/fraud.py`
  - *Validation:* `pytest tests/tools/mock/test_fraud.py` (TC-07)
- [x] **TASK-10:** Implement `MockRefundService` (getRefundStatus, initiateRefund)
  - *Files:* `app/tools/mock/refund.py`
  - *Validation:* `pytest tests/tools/mock/test_refund.py` (TC-08, TC-09)

### Phase 4: Mock Adapters — Write Tools
- [ ] **TASK-11:** Implement `MockTicketService` (createSupportTicket)
  - *Files:* `app/tools/mock/ticket.py`
  - *Validation:* `pytest tests/tools/mock/test_ticket.py`
- [ ] **TASK-12:** Implement `MockNotificationService` (sendNotification) — logs only in mock mode
  - *Files:* `app/tools/mock/notification.py`
  - *Validation:* `pytest tests/tools/mock/test_notification.py`
- [ ] **TASK-13:** Implement `MockEscalationService` (escalateToHumanAgent)
  - *Files:* `app/tools/mock/escalation.py`

### Phase 5: Tool Service Factory & Router
- [ ] **TASK-14:** Implement `ToolServiceFactory` — reads `TOOL_MODE` env var and creates appropriate adapters
  - *Files:* `app/tools/factory.py`
  - *Validation:* `pytest tests/tools/test_factory.py` — test mock, live, hybrid mode selection
- [ ] **TASK-15:** Implement `ToolRouter` with **session-injected `user_id`** and **idempotency key** support
  - *Files:* `app/agent/tool_router.py`
  - *Details:* ToolRouter strips any `user_id` from LLM args and injects from authenticated session context. Write tools auto-generate idempotency keys via `sha256(session_id + tool_name + sorted_args)` and check Redis cache before execution.
  - *Validation:* `pytest tests/agent/test_tool_router.py` — tenant isolation and idempotency tests pass
- [ ] **TASK-16:** Create `ToolRegistry` — consolidates all Pydantic schemas into Gemini-compatible function definitions. **Ensure `user_id` is NOT in any tool schema exposed to the LLM.**
  - *Files:* `app/tools/registry.py`
  - *Validation:* Verify generated JSON schemas match Gemini function calling format AND do not include `user_id` parameter

### Phase 5.5: Production Safety — Currency, Isolation & Idempotency
- [ ] **TASK-16a:** Implement `rupees_to_paise()` and `paise_to_rupees()` conversion utilities
  - *Files:* `app/tools/converters.py`
  - *Validation:* `pytest tests/tools/test_converters.py` — ₹5,000 → 500000 paise, edge cases (0, negative, very large amounts)
- [ ] **TASK-16b:** Wire currency conversion into all monetary tool adapters (getTransaction, getAccountBalance, initiateRefund, getRefundStatus)
  - *Details:* Adapters receive rupees from LLM, convert to paise for DB/API, convert back to rupees for ToolResult
  - *Validation:* Integration tests with seed data verify correct amounts returned in rupees
- [ ] **TASK-16c:** Add Pydantic validators for monetary fields — reject negative amounts and amounts > ₹10,00,000
  - *Files:* `app/tools/schemas.py`
  - *Validation:* `pytest tests/tools/test_schemas.py` — validator tests
- [ ] **TASK-16d:** Implement idempotency key cache layer in Redis for write tools
  - *Files:* `app/agent/tool_router.py`, `app/core/idempotency.py`
  - *Details:* Redis key: `idempotency:{sha256_key}`, TTL: refund=24h, ticket=1h, notification=5m
  - *Validation:* `pytest tests/agent/test_idempotency.py` — duplicate calls return cached result

### Phase 6: Live Adapter Stubs (Interface Only)
- [ ] **TASK-17:** Create live adapter stub files with `NotImplementedError` for each tool
  - *Files:* `app/tools/live/transaction.py`, `app/tools/live/account.py`, `app/tools/live/payment.py`, `app/tools/live/fraud.py`, `app/tools/live/refund.py`, `app/tools/live/ticket.py`, `app/tools/live/notification.py`
  - *Validation:* All stubs inherit from the correct ABC and raise `NotImplementedError`
- [ ] **TASK-18:** Add infrastructure helpers for live mode: circuit breaker base, retry decorator, response cache
  - *Files:* `app/tools/live/infra.py`
  - *Validation:* Unit tests for circuit breaker and retry logic

### Phase 7: Testing & Verification
- [ ] **TASK-19:** Write integration tests for all mock adapters against PostgreSQL fixtures
  - *Files:* `tests/tools/integration/`
  - *Validation:* `pytest tests/tools/integration/ -v` all pass
- [ ] **TASK-20:** Write access control tests (cross-user data isolation)
  - *Files:* `tests/tools/test_access_control.py`
  - *Validation:* User A cannot access User B's transactions
- [ ] **TASK-21:** Validate Gemini function calling schema generation
  - *Files:* `tests/tools/test_registry.py`
  - *Validation:* Generated schemas are valid JSON Schema and match Gemini API format
- [ ] **TASK-22:** Update Master Spec in [main-spec.md](../../specs/main-spec.md) and mark feature as `DESIGN_READY`
  - *Validation:* Feature status updated in main spec and features/README.md

---

## 4. Blocker & Risk Log

| Date | Blocker / Issue | Impact | Resolution / Next Step | Resolved? |
| :--- | :--- | :--- | :--- | :--- |
| - | None | - | - | [ ] |
