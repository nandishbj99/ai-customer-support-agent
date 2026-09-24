from app.agent.llm.types import LLMChunk, LLMResponse, TokenUsage, ToolCall


def test_token_usage_defaults():
    usage = TokenUsage()
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0


def test_tool_call_model():
    tc = ToolCall(id="call_123", name="getTransaction", arguments={"transaction_id": "tx_001"})
    assert tc.id == "call_123"
    assert tc.name == "getTransaction"
    assert tc.arguments["transaction_id"] == "tx_001"


def test_llm_response_helpers():
    resp_text = LLMResponse(text="Hello", finish_reason="stop")
    assert not resp_text.has_tool_calls
    assert resp_text.text == "Hello"

    resp_tools = LLMResponse(
        tool_calls=[ToolCall(id="c1", name="getAccount", arguments={})],
        finish_reason="tool_call",
    )
    assert resp_tools.has_tool_calls
    assert len(resp_tools.tool_calls) == 1


def test_llm_chunk():
    chunk = LLMChunk(delta_text=" partial ", finish_reason=None)
    assert chunk.delta_text == " partial "
    assert chunk.finish_reason is None
