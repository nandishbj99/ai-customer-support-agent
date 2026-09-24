# Phased Execution Plan: FEAT-001 Core Agent Orchestrator

> **Feature ID:** `FEAT-001-agent-orchestrator`  
> **Status:** `COMPLETED`  
> **Current Focus / Next Action:** `Integrated with Fintech Tools; ready for RAG (FEAT-003) & HITL (FEAT-004)`  
> **Owner:** `Team`  
> **Last Updated:** 2026-09-24

---

## Phase 1: Project Setup & Baseline
- [x] TASK 1.1: Initialize Python project, FastAPI skeleton, and basic folder structure.
- [x] TASK 1.2: Define basic Pydantic models for request/response payloads (`LLMResponse`, `ToolCall`, `LLMChunk`, `TokenUsage`).
- [x] TASK 1.3: Set up environment configuration (`LLM_PROVIDER`, `LLM_MODEL`, API keys via `.env`).

## Phase 2: LLM Provider Abstraction Layer
- [x] TASK 2.1: Define abstract `LLMProviderBase` ABC with `generate()`, `generate_stream()`, `get_model_name()`, `get_max_tokens()`.
  - *Files:* `app/agent/llm/base.py`
  - *Validation:* ABC is importable, methods have `@abstractmethod` decorators
- [x] TASK 2.2: Implement `GeminiProvider` — default LLM adapter using `google-genai` SDK.
  - *Files:* `app/agent/llm/gemini.py`
  - *Validation:* `pytest tests/agent/llm/test_gemini.py` — mock API calls pass
- [x] TASK 2.3: Implement function calling format conversion: Pydantic tool schemas → Gemini `FunctionDeclaration` format.
  - *Files:* `app/agent/llm/gemini.py` (`_convert_tools()`, `_convert_messages()`, `_normalize_response()`)
  - *Validation:* Round-trip test: Pydantic → Gemini → normalized `ToolCall`
- [x] TASK 2.4: Create provider stubs for OpenAI, Anthropic, Ollama (raise `NotImplementedError`).
  - *Files:* `app/agent/llm/openai.py`, `app/agent/llm/anthropic.py`, `app/agent/llm/ollama.py`
  - *Validation:* All stubs inherit from `LLMProviderBase`
- [x] TASK 2.5: Implement `LLMProviderFactory` — reads `LLM_PROVIDER` env var, returns correct adapter.
  - *Files:* `app/agent/llm/factory.py`
  - *Validation:* `pytest tests/agent/llm/test_factory.py` — factory returns correct provider type

## Phase 3: Core ReAct Loop
- [x] TASK 3.1: Implement the base prompt template for the fintech support agent persona (`app/agent/prompts.py`).
- [x] TASK 3.2: Implement the ReAct while-loop (maximum 5 iterations) calling `LLMProviderBase.generate()` — NOT Gemini directly.
- [x] TASK 3.3: Implement parsing of normalized `LLMResponse` to separate tool calls from final answers.
- [x] TASK 3.4: Add hard limits (5 iterations max, 10 tool calls max) and timeout handling for the LLM call.

## Phase 4: Tool Dispatch System
- [x] TASK 4.1: Implement the Tool Registry — consolidates Pydantic schemas into a canonical format consumable by any LLM provider (`app/tools/registry.py`).
- [x] TASK 4.2: Implement the Tool Dispatcher — parses `ToolCall` from `LLMResponse`, executes the target service, formats the output as an Observation (`app/agent/tool_router.py`).
- [x] TASK 4.3: Wire tool schemas through the provider adapter's format conversion (Pydantic → provider-native).

## Phase 5: State Management
- [x] TASK 5.1: Integrate Redis for fast session state retrieval and storage with TTL (`app/agent/state.py`).
- [x] TASK 5.2: Implement context window management (sliding window truncation of messages when token limits are approached).
- [ ] TASK 5.3: Set up background worker / audit service to persist completed conversations to PostgreSQL (FEAT-005/FEAT-006).

## Phase 6: Error Handling & Fallbacks
- [x] TASK 6.1: Implement graceful fallback messages when the LLM provider returns an error or timeout.
- [x] TASK 6.2: Implement confidence score evaluation heuristics.
- [x] TASK 6.3: Build logic to trigger HITL escalation if confidence is low or safety rules are breached.

## Phase 7: Testing & Verification
- [x] TASK 7.1: Write unit tests for `LLMProviderBase`, `GeminiProvider`, and `LLMProviderFactory`.
- [x] TASK 7.2: Write unit tests for ReAct loop parsing and Tool Dispatch logic using `MockLLMProvider`.
- [x] TASK 7.3: Create mock tools and write integration tests for a full multi-turn conversation and S-01 seed scenario.
- [x] TASK 7.4: Write adapter contract tests — verify all providers return identical `LLMResponse` schema.
- [x] TASK 7.5: Verify FastAPI endpoint `POST /api/v1/chat/message` with dependency injection.

