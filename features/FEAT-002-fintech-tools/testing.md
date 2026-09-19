# Feature Testing & Verification: FEAT-002 — Fintech Tool Layer

> **Feature ID:** `FEAT-002-fintech-tools`  
> **Status:** `PENDING_EXECUTION`  
> **Spec Reference:** [Feature Spec](./spec.md) | [Design & ADRs](./design.md)

---

## 1. Verification Strategy

Testing covers three layers:
1. **Unit Tests:** Individual Pydantic validation, service layer logic (mocked DB), adapter interface compliance.
2. **Integration Tests:** End-to-end tool execution against real PostgreSQL with fixtures.
3. **Adapter Contract Tests:** Verify both mock and live adapters produce identical `ToolResult` schemas.
4. **Security Tests:** Cross-user data isolation, injection prevention, rate limiting.

---

## 2. Test Case Matrix

### 2.1 Unit Tests — Schemas & Validation
| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | Valid `getTransaction` input | `tools.schemas` | Pydantic model accepts and validates | `PENDING` |
| `TC-02` | Missing required `txn_id` and `user_id` | `tools.schemas` | Pydantic `ValidationError` raised | `PENDING` |
| `TC-03` | Negative refund amount in `initiateRefund` | `tools.schemas` | Pydantic rejects with clear error | `PENDING` |
| `TC-04` | `.model_json_schema()` generates valid Gemini schema | `tools.schemas` | Valid JSON Schema for all 13 tools | `PENDING` |

### 2.2 Unit Tests — Mock Adapter Logic
| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-05` | `getTransaction` with valid txn_id | `tools.mock.transaction` | Returns `ToolResult(success=True)` with transaction data | `PENDING` |
| `TC-06` | `getTransaction` with non-existent txn_id | `tools.mock.transaction` | Returns `ToolResult(success=False, error={code: "TXN_NOT_FOUND"})` | `PENDING` |
| `TC-07` | `checkFraudStatus` for flagged transaction | `tools.mock.fraud` | Returns `{is_flagged: true, risk_score: >0.7}` | `PENDING` |
| `TC-08` | `initiateRefund` with amount > ₹10,000 | `tools.mock.refund` | Returns `{status: "pending_approval"}`, routes to HITL | `PENDING` |
| `TC-09` | `initiateRefund` with amount ≤ ₹10,000 | `tools.mock.refund` | Returns `{status: "processing"}`, auto-approved | `PENDING` |
| `TC-10` | `getAccount` for frozen account | `tools.mock.account` | Returns `{status: "frozen"}` | `PENDING` |

### 2.3 Adapter Contract Tests
| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-11` | All mock adapters inherit from correct ABC | `tools.mock.*` | `isinstance(service, ServiceBase)` is True | `PENDING` |
| `TC-12` | All live adapter stubs inherit from correct ABC | `tools.live.*` | `isinstance(service, ServiceBase)` is True | `PENDING` |
| `TC-13` | Mock and live adapters return same `ToolResult` schema | `tools.*` | Both return `{success, data, error}` structure | `PENDING` |

### 2.4 Factory & Router Tests
| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-14` | Factory creates mock adapters when `TOOL_MODE=mock` | `tools.factory` | All services are `Mock*Service` instances | `PENDING` |
| `TC-15` | Factory creates live adapters when `TOOL_MODE=live` | `tools.factory` | All services are `*LiveService` instances | `PENDING` |
| `TC-16` | Factory handles hybrid mode correctly | `tools.factory` | Mix of mock and live per tool config | `PENDING` |
| `TC-17` | ToolRouter dispatches `getTransaction` to correct service | `agent.tool_router` | Correct service method invoked | `PENDING` |
| `TC-18` | ToolRouter handles unknown tool name | `agent.tool_router` | Returns `ToolResult(success=False, error={code: "UNKNOWN_TOOL"})` | `PENDING` |

### 2.5 Integration Tests (PostgreSQL Fixtures)
| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-19` | `getTransaction` retrieves accurate joined data | Full mock pipeline | Amount, status, merchant all correct | `PENDING` |
| `TC-20` | `getTransactionHistory` with pagination | Full mock pipeline | Returns correct page size, `has_more` flag | `PENDING` |
| `TC-21` | `checkFraudStatus` returns correct score from fixtures | Full mock pipeline | Score matches seeded data | `PENDING` |
| `TC-22` | End-to-end: Router → Factory → Mock → DB → ToolResult | Full pipeline | Complete round-trip successful | `PENDING` |

### 2.6 Security & Access Control Tests
| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-23` | User A tries to access User B's transaction | `tools.mock.transaction` | Returns `UNAUTHORIZED_ACCESS` error | `PENDING` |
| `TC-24` | SQL injection in `txn_id` field | `tools.schemas` | Pydantic validation rejects | `PENDING` |
| `TC-25` | Rate limit exceeded for read operations | Rate limiter | Returns `RATE_LIMITED` error after 50 calls/min | `PENDING` |

### 2.7 Live Adapter Infrastructure Tests
| Test ID | Test Scenario | Target Module | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-26` | Circuit breaker opens after 5 failures | `tools.live.infra` | Subsequent calls return `SERVICE_UNAVAILABLE` | `PENDING` |
| `TC-27` | Circuit breaker resets after 60s timeout | `tools.live.infra` | Calls resume normally | `PENDING` |
| `TC-28` | Retry with exponential backoff on 5xx | `tools.live.infra` | Max 3 retries with increasing delay | `PENDING` |
| `TC-29` | No retry on 4xx client error | `tools.live.infra` | Immediate failure, no retry | `PENDING` |
| `TC-30` | Response cache returns cached data within TTL | `tools.live.infra` | Second call uses Redis cache | `PENDING` |

---

## 3. Test Data Strategy

- Maintain a static set of realistic SQL fixtures in `tests/fixtures/seed_scenarios.sql`
- Use deterministic IDs in tests (e.g., `user_001`, `txn_001`) for straightforward assertions
- Fixtures cover these scenarios:

| Scenario ID | User | Transaction | Account | Fraud | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S-01 | `user_001` | ₹5,000 FAILED (insufficient funds) | Balance ₹3,200 | Clean | Agent explains balance |
| S-02 | `user_002` | ₹25,000 BLOCKED | Balance ₹50,000 | Flagged (0.87) | Agent detects fraud |
| S-03 | `user_003` | ₹1,200 REFUNDED | Active | Clean | Agent checks refund |
| S-04 | `user_004` | ₹15,000 FAILED | Active | Clean | HITL trigger (> ₹10K) |
| S-05 | `user_005` | None | Frozen | N/A | Agent explains frozen account |

---

## 4. Acceptance Criteria Checklist
- [ ] All 13 mock adapters implemented and inherit from correct ABCs
- [ ] All 7 live adapter stubs created (raise `NotImplementedError`)
- [ ] Factory correctly selects adapters based on `TOOL_MODE`
- [ ] ToolRouter dispatches all 13 tools correctly
- [ ] Gemini function calling schemas generated for all tools
- [ ] Cross-user data isolation enforced (TC-23)
- [ ] Circuit breaker and retry logic unit tested (TC-26-29)
- [ ] Coverage > 90% for the tool layer
- [ ] No regressions in existing test suites

---

## 5. Test Execution Sign-Off
- **Executed By:** `<Name / Agent>`
- **Execution Date:** TBD
- **Final Result:** `PENDING`
- **Notes / Observations:** —
