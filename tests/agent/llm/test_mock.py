import pytest

from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.types import LLMResponse, ToolCall


@pytest.mark.asyncio
async def test_mock_provider_echo():
    mock = MockLLMProvider()
    resp = await mock.generate([{"role": "user", "content": "Help with refund"}])
    assert resp.text == "Mock response to: Help with refund"
    assert resp.finish_reason == "stop"
    assert not resp.has_tool_calls
    assert len(mock.call_history) == 1


@pytest.mark.asyncio
async def test_mock_provider_canned_queue():
    mock = MockLLMProvider()
    mock.add_response(
        LLMResponse(
            tool_calls=[ToolCall(id="call_1", name="getTransaction", arguments={"transaction_id": "tx_123"})],
            finish_reason="tool_call",
        )
    )
    mock.add_response(
        LLMResponse(
            text="Your transaction was successful.",
            finish_reason="stop",
        )
    )

    r1 = await mock.generate([{"role": "user", "content": "check tx"}])
    assert r1.has_tool_calls
    assert r1.tool_calls[0].name == "getTransaction"

    r2 = await mock.generate([{"role": "tool", "content": "status: success"}])
    assert not r2.has_tool_calls
    assert r2.text == "Your transaction was successful."


@pytest.mark.asyncio
async def test_mock_provider_streaming():
    mock = MockLLMProvider()
    mock.add_response(LLMResponse(text="Hello world!", finish_reason="stop"))

    chunks = []
    async for chunk in mock.generate_stream([{"role": "user", "content": "hi"}]):
        chunks.append(chunk)

    assert len(chunks) == 2
    full_text = "".join(c.delta_text for c in chunks if c.delta_text)
    assert full_text == "Hello world!"
