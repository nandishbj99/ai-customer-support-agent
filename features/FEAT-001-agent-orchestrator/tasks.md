# Phased Execution Plan: FEAT-001 Core Agent Orchestrator

> **Feature ID:** `FEAT-001-agent-orchestrator`  
> **Status:** `PROPOSED`  
> **Current Focus / Next Action:** `Review ADRs & Design (LLM Provider Abstraction) with user`  
> **Owner:** `Team`  
> **Last Updated:** 2026-09-22

---

## Phase 1: Project Setup & Baseline
- [ ] TASK 1.1: Initialize Python project, FastAPI skeleton, and basic folder structure.
- [ ] TASK 1.2: Define basic Pydantic models for request/response payloads (`LLMResponse`, `ToolCall`, `LLMChunk`, `TokenUsage`).
- [ ] TASK 1.3: Set up environment configuration (`LLM_PROVIDER`, `LLM_MODEL`, API keys via `.env`).

## Phase 2: LLM Provider Abstraction Layer
- [ ] TASK 2.1: Define abstract `LLMProviderBase` ABC with `generate()`, `generate_stream()`, `get_model_name()`, `get_max_tokens()`.
  - *Files:* `app/agent/llm/base.py`
  - *Validation:* ABC is importable, methods have `@abstractmethod` decorators
- [ ] TASK 2.2: Implement `GeminiProvider` — default LLM adapter using `google-genai` SDK.
  - *Files:* `app/agent/llm/gemini.py`
  - *Validation:* `pytest tests/agent/llm/test_gemini.py` — mock API calls pass
- [ ] TASK 2.3: Implement function calling format conversion: Pydantic tool schemas → Gemini `FunctionDeclaration` format.
  - *Files:* `app/agent/llm/gemini.py` (`_to_gemini_tool()`, `_normalize()`)
  - *Validation:* Round-trip test: Pydantic → Gemini → normalized `ToolCall`
- [ ] TASK 2.4: Create provider stubs for OpenAI, Anthropic, Ollama (raise `NotImplementedError`).
  - *Files:* `app/agent/llm/openai.py`, `app/agent/llm/anthropic.py`, `app/agent/llm/ollama.py`
  - *Validation:* All stubs inherit from `LLMProviderBase`
- [ ] TASK 2.5: Implement `LLMProviderFactory` — reads `LLM_PROVIDER` env var, returns correct adapter.
  - *Files:* `app/agent/llm/factory.py`
  - *Validation:* `pytest tests/agent/llm/test_factory.py` — factory returns correct provider type

## Phase 3: Core ReAct Loop
- [ ] TASK 3.1: Implement the base prompt template for the fintech support agent persona.
- [ ] TASK 3.2: Implement the ReAct while-loop (maximum 5 iterations) calling `LLMProviderBase.generate()` — NOT Gemini directly.
- [ ] TASK 3.3: Implement parsing of normalized `LLMResponse` to separate tool calls from final answers.
- [ ] TASK 3.4: Add hard limits and timeout handling for the LLM call.

## Phase 4: Tool Dispatch System
- [ ] TASK 4.1: Implement the Tool Registry — consolidates Pydantic schemas into a canonical format consumable by any LLM provider.
- [ ] TASK 4.2: Implement the Tool Dispatcher — parses `ToolCall` from `LLMResponse`, executes the target service, formats the output as an Observation.
- [ ] TASK 4.3: Wire tool schemas through the provider adapter's format conversion (Pydantic → provider-native).

## Phase 5: State Management
- [ ] TASK 5.1: Integrate Redis for fast session state retrieval and storage (with TTL).
- [ ] TASK 5.2: Implement context window management (truncating or summarizing messages when token limits are approached).
- [ ] TASK 5.3: Set up background Celery task to persist completed conversations to PostgreSQL.

## Phase 6: Error Handling & Fallbacks
- [ ] TASK 6.1: Implement graceful fallback messages when the LLM provider returns an error or rate limit.
- [ ] TASK 6.2: Implement confidence score evaluation heuristics.
- [ ] TASK 6.3: Build logic to trigger HITL escalation if confidence is low or safety rules are breached.

## Phase 7: Testing & Verification
- [ ] TASK 7.1: Write unit tests for `LLMProviderBase`, `GeminiProvider`, and `LLMProviderFactory`.
- [ ] TASK 7.2: Write unit tests for ReAct loop parsing and Tool Dispatch logic using `MockLLMProvider`.
- [ ] TASK 7.3: Create mock tools and write integration tests for a full multi-turn conversation.
- [ ] TASK 7.4: Write adapter contract tests — verify all providers return identical `LLMResponse` schema.
- [ ] TASK 7.5: Perform load testing on the orchestrator endpoints using simulated concurrent users.
