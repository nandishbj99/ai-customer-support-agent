# FEAT-002-fintech-tools: Design & ADRs

## Overview
This document outlines the architectural decisions and design patterns for the Fintech Tool Layer, which exposes deterministic capabilities to the LLM agent.

## ADR-01: Tool Interface Pattern - Direct DB Queries vs Service Layer vs Microservice Calls

### Context
The LLM agent needs to interact with fintech data (transactions, accounts) and trigger actions (refunds). We need a pattern to expose these capabilities cleanly without tightly coupling the LLM loop to database internals.

### Options
1. **Direct SQLAlchemy Queries:** Tools execute raw or ORM queries directly within the tool handler.
2. **Service Layer Pattern (Repository):** Tools call intermediate Python service classes (e.g., `TransactionService.get(id)`), which abstract the data access.
3. **gRPC Microservices:** Tools act as clients calling external gRPC services (simulating a real enterprise environment).

### Decision
**Recommend: Service Layer Pattern (Option 2)**

### Rationale
- **Pros:** Clean separation of concerns. Easy to test the tools by mocking the service layer. Avoids the overhead of deploying and managing multiple microservices for a V1 prototype.
- **Cons:** Less realistic than full microservices for a large enterprise, but perfect for a monolithic FastAPI backend.

## ADR-02: Mock vs Real Data Strategy - How to simulate fintech data

### Context
To test the agent's ability to reason over transactions and accounts, we need a consistent and realistic dataset.

### Options
1. **In-memory mock data:** Hardcoded Python dictionaries.
2. **SQLite with seed data:** Lightweight DB for local dev.
3. **PostgreSQL with fixtures:** Same DB engine as production, seeded with realistic data scripts.

### Decision
**Recommend: PostgreSQL with fixtures (Option 3)**

### Rationale
- **Pros:** Full feature parity with production (JSONB columns, advanced indexing, transactional guarantees). Realistic testing of SQLAlchemy models and migrations.
- **Cons:** Requires a running PostgreSQL instance (via Docker) even for local dev.

## ADR-03: Tool Schema Definition - JSON Schema vs Pydantic vs Protobuf

### Context
Gemini function calling requires strict JSON Schema definitions for tools.

### Options
1. **Raw JSON schema:** Manually writing dicts matching JSON Schema spec.
2. **Pydantic models:** Define inputs/outputs as Pydantic models and use `.model_json_schema()` to auto-generate the tool schemas.
3. **Protobuf:** Define messages in `.proto` files.

### Decision
**Recommend: Pydantic models (Option 2)**

### Rationale
- **Pros:** Strong typing in Python. Native integration with FastAPI. Automatic, error-free generation of JSON Schema for Gemini. Built-in input validation.
- **Cons:** Slight learning curve if using advanced Pydantic v2 features.

## ADR-04: Error Handling - Tool-Level Error Codes & Retry Strategy

### Context
Tools may fail due to DB timeouts, invalid input, or business rule violations. The LLM needs to understand these failures to act appropriately (e.g., tell the user, or try a different approach).

### Decision
1. **Standard Output Wrapper:** Every tool returns a structured response: `{"success": bool, "data": dict|null, "error": {"code": str, "message": str}|null}`.
2. **Semantic Error Codes:** Use predictable codes (`TXN_NOT_FOUND`, `INSUFFICIENT_FUNDS`) rather than HTTP status codes, so the LLM can branch its logic based on the code.
3. **LLM Retry Strategy:** If a tool fails with `INVALID_INPUT`, the LLM prompt instructions will dictate that it should re-evaluate the arguments and try once more before telling the user it cannot complete the action.
4. **Circuit Breaker:** For external service simulations (like payment gateways), implement a basic circuit breaker in the Service Layer.
