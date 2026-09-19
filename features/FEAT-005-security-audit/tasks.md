# Phased Execution Plan: FEAT-005-security-audit

## Phase 1: Authentication & Authorization Foundations
*   [ ] **Task 1.1:** Setup JWT authentication for customers (FastAPI dependency, PyJWT, token generation/validation).
*   [ ] **Task 1.2:** Implement Redis-backed refresh token logic (storage, rotation, revocation).
*   [ ] **Task 1.3:** Implement OAuth2/OIDC integration for internal agents (auth code flow with PKCE).
*   [ ] **Task 1.4:** Define RBAC models and implement `@requires_role` decorators/dependencies for FastAPI.
*   [ ] **Task 1.5:** Implement internal API key authentication mechanism and lifecycle management.

## Phase 2: Core Security & Hardening
*   [ ] **Task 2.1:** Implement rate limiting using Redis (Token bucket or sliding window algorithm per user/IP).
*   [ ] **Task 2.2:** Configure robust CORS policies for web clients.
*   [ ] **Task 2.3:** Implement a middleware to inject strict HTTP security headers (CSP, HSTS, etc.).
*   [ ] **Task 2.4:** Implement session management features (idle timeouts, max session limits, remote kill).
*   [ ] **Task 2.5:** Standardize global input sanitization middleware to prevent injection attacks.

## Phase 3: Audit Logging & PII Masking
*   [ ] **Task 3.1:** Setup `structlog` for structured JSON logging.
*   [ ] **Task 3.2:** Develop custom `structlog` processors for regex-based and field-based PII redaction.
*   [ ] **Task 3.3:** Design and create SQLAlchemy models + Alembic migrations for the `audit_logs` table.
*   [ ] **Task 3.4:** Create an asynchronous Audit Service (via Celery) to write to the `audit_logs` table without blocking API responses.
*   [ ] **Task 3.5:** Implement Request/Response logging middleware, integrating the PII redactor.

## Phase 4: LLM Security & Prompt Injection Defense
*   [ ] **Task 4.1:** Implement input-filtering layer for user messages (regex/heuristics for prompt injection detection).
*   [ ] **Task 4.2:** Develop the Output Guardrail layer to evaluate LLM ReAct plans prior to tool execution.
*   [ ] **Task 4.3:** Ensure tenant-isolation in tool APIs (RBAC context passed into every tool call).

## Phase 5: Testing, Benchmarking & Review
*   [ ] **Task 5.1:** Write comprehensive unit and integration tests (see `testing.md`).
*   [ ] **Task 5.2:** Conduct performance benchmarking to ensure auth overhead < 10ms and audit write < 5ms.
*   [ ] **Task 5.3:** Security review and automated vulnerability scanning.
