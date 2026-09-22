# Feature Specification: FEAT-001 Core Agent Orchestrator

## 1. Overview
This feature implements the central brain of the AI-powered fintech customer support agent. The orchestrator receives natural language inputs, maintains conversation state, reasons about the user's intent, and acts by executing various internal APIs (tools) to fulfill the request.

## 2. User Stories
*   **US-01 (Customer - Inquiry):** As a fintech customer, I want to ask questions about my account or payments in natural language, so that I can get immediate answers without navigating complex menus.
*   **US-02 (Customer - Issue Resolution):** As a customer, I want the agent to investigate specific problems (e.g., "Why was my payment rejected?"), so that I don't have to wait for a human agent.
*   **US-03 (System - Tool Execution):** As the orchestrator, I need to securely call internal APIs (transaction lookup, fraud checks) on behalf of the customer, so I can fetch accurate data to answer queries.
*   **US-04 (Customer - Multi-turn):** As a customer, I want the agent to remember context from earlier in our conversation, so I don't have to repeat myself.

## 3. Functional Requirements
*   **FR-01: ReAct Loop Implementation:** Implement a Reason+Act loop using the Google Gemini model.
*   **FR-02: Tool Calling:** Support seamless native function calling using Gemini's API to interact with downstream fintech services.
*   **FR-03: Multi-step Reasoning:** The agent must be able to create a plan, execute a tool, observe the result, and decide the next step dynamically.
*   **FR-04: Conversation State Management:** Maintain active session state, including user metadata, conversation history, and tool outputs.
*   **FR-05: Response Synthesis:** Synthesize final responses back to the user after collecting all necessary tool results.
*   **FR-06: Graceful Fallback:** Provide a standard fallback response if the LLM provider is unavailable or times out.
*   **FR-07: Max Reasoning Steps Limit:** Implement a hard limit on ReAct iterations (e.g., max 5 loops) to prevent infinite loops and runaway costs.
*   **FR-08: Confidence Scoring:** Generate or infer a confidence score for the proposed final answer based on tool execution success and LLM output.
*   **FR-09: Human Escalation:** If confidence is below a configurable threshold, gracefully escalate to a human agent, providing a summary of the conversation.
*   **FR-10: Context Window Management:** Implement automatic summarization of conversation history when approaching the LLM token limit.

## 4. Non-Functional Requirements (NFRs)
*   **NFR-01: Latency:** P95 response time for the orchestrator (excluding external tool latency) must be under 5 seconds.
*   **NFR-02: Concurrency:** The orchestrator must support at least 100 concurrent active chat sessions.
*   **NFR-03: Resource Limits:** Maximum of 10 tool calls per user query.
*   **NFR-04: Security:** PII and sensitive financial data must not be logged in plain text.

## 5. API Contracts

### 5.1 POST `/api/v1/chat/message`
**Request:**
```json
{
  "session_id": "uuid-v4",
  "customer_id": "cust_12345",
  "message": "Why was my last payment of ₹500 rejected?",
  "metadata": {}
}
```

**Response:**
```json
{
  "session_id": "uuid-v4",
  "message_id": "msg_9876",
  "response": "Your payment of ₹500 to Merchant X was rejected due to insufficient funds in your wallet. Your current balance is ₹230.",
  "status": "success",
  "confidence_score": 0.95,
  "escalated": false,
  "tool_calls_made": ["get_last_transaction", "get_account_balance"]
}
```

---

## 6. LLM Provider Abstraction Requirements

### FR-11: Abstract LLM Interface
- **Description:** Define an abstract base class `LLMProviderBase` with `generate()` and `generate_stream()` methods.
- **Implementation:** Python `abc.ABC` with `@abstractmethod` decorators.
- **Rationale:** The ReAct loop, tool dispatch, and state management must be completely provider-agnostic.

### FR-12: Default Provider — Google Gemini
- **Description:** Implement `GeminiProvider` as the default LLM adapter using the `google-genai` SDK.
- **Models Supported:** `gemini-2.5-flash` (default), `gemini-2.5-pro`, `gemini-2.0-flash`.
- **Activation:** `LLM_PROVIDER=gemini` (default).

### FR-13: Provider Stubs (Future-Ready)
- **Description:** Create stub adapters for OpenAI, Anthropic, and Ollama (local) with `NotImplementedError`.
- **Files:** `agent/llm/openai.py`, `agent/llm/anthropic.py`, `agent/llm/ollama.py`
- **Purpose:** Ready-made extension points for future provider integration.

### FR-14: LLM Provider Factory
- **Description:** A factory class that reads `LLM_PROVIDER` env var and instantiates the correct provider.
- **Supported values:** `gemini` (default), `openai`, `anthropic`, `local`.
- **Dependency Injection:** Factory provides the LLM provider to the orchestrator via FastAPI dependency injection.

### FR-15: Normalized LLM Response
- **Description:** All provider adapters must return a unified `LLMResponse` dataclass containing: `text`, `tool_calls` (list of `ToolCall`), `finish_reason`, and `usage` (token counts).
- **Rationale:** The orchestrator must not contain any provider-specific parsing logic.

### FR-16: Function Calling Format Normalization
- **Description:** Each provider adapter must translate canonical Pydantic tool schemas to the provider's native function calling format (Gemini `FunctionDeclaration`, OpenAI `tools`, Anthropic `input_schema`).
- **Direction:** Pydantic → Provider-specific (outbound). Provider-response → `ToolCall` dataclass (inbound).

### FR-17: Streaming Support
- **Description:** `generate_stream()` must return an `AsyncIterator[LLMChunk]` for real-time response streaming via WebSocket (FEAT-006).
- **Chunking:** Stream semantic chunks (sentences/paragraphs), not raw tokens.

### FR-18: Multi-Model Routing (Future)
- **Description:** Support routing different query complexities to different models (e.g., Gemini Flash for simple balance checks, Gemini Pro for complex fraud investigations).
- **Scope:** Design the interface now; implement routing logic in a future iteration.

