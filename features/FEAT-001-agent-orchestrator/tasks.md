# Phased Execution Plan: FEAT-001 Core Agent Orchestrator

## Phase 1: Project Setup & Baseline
- [ ] TASK 1.1: Initialize Python project, FastAPI skeleton, and basic folder structure.
- [ ] TASK 1.2: Set up `google-genai` SDK and configure API keys securely via environment variables.
- [ ] TASK 1.3: Define basic Pydantic models for request/response payloads.

## Phase 2: Core ReAct Loop
- [ ] TASK 2.1: Implement the base prompt template for the support agent persona.
- [ ] TASK 2.2: Implement the while-loop for ReAct iterations (maximum 5 loops).
- [ ] TASK 2.3: Implement parsing of Gemini's response to separate reasoning from final answers.
- [ ] TASK 2.4: Add hard limits and timeout handling for the LLM call.

## Phase 3: Tool Dispatch System
- [ ] TASK 3.1: Create an abstract `BaseTool` class / interface.
- [ ] TASK 3.2: Implement a lightweight Tool Registry to dynamically load and expose tool schemas to Gemini.
- [ ] TASK 3.3: Implement the Tool Dispatcher to parse LLM function calls, execute the target Python function, and format the output as an Observation.

## Phase 4: State Management
- [ ] TASK 4.1: Integrate Redis for fast session state retrieval and storage (with TTL).
- [ ] TASK 4.2: Implement context window management (truncating or summarizing messages when token limits are approached).
- [ ] TASK 4.3: Set up background Celery task to persist completed conversations to PostgreSQL.

## Phase 5: Error Handling & Fallbacks
- [ ] TASK 5.1: Implement graceful fallback messages when Gemini returns an error or rate limit.
- [ ] TASK 5.2: Implement confidence score evaluation heuristics.
- [ ] TASK 5.3: Build logic to trigger Human-in-the-Loop (HITL) escalation if confidence is low or specific safety rules are breached.

## Phase 6: Testing & Verification
- [ ] TASK 6.1: Write unit tests for ReAct parsing and Tool Dispatch logic.
- [ ] TASK 6.2: Create mock tools and write integration tests for a full multi-turn conversation.
- [ ] TASK 6.3: Perform load testing on the orchestrator endpoints using simulated concurrent users.
