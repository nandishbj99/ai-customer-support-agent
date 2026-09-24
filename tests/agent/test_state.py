import pytest

from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.types import LLMResponse
from app.agent.orchestrator import AgentOrchestrator
from app.agent.state import SessionState, SessionStateManager


@pytest.mark.asyncio
async def test_session_state_lifecycle():
    manager = SessionStateManager()

    session = await manager.get_or_create_session("sess_001", "cust_123")
    assert session.session_id == "sess_001"
    assert session.customer_id == "cust_123"
    assert session.messages == []

    await manager.append_message("sess_001", {"role": "user", "content": "Hello"})
    updated = await manager.get_session("sess_001")
    assert len(updated.messages) == 1
    assert updated.messages[0]["content"] == "Hello"

    await manager.clear_session("sess_001")
    assert await manager.get_session("sess_001") is None


def test_sliding_window_truncation():
    manager = SessionStateManager(max_messages=4)
    messages = [
        {"role": "user", "content": f"msg {i}"} for i in range(10)
    ]
    truncated = manager.truncate_history(messages)
    assert len(truncated) == 4
    assert truncated[0]["content"] == "msg 6"
    assert truncated[-1]["content"] == "msg 9"


@pytest.mark.asyncio
async def test_orchestrator_multi_turn_session_preservation():
    manager = SessionStateManager()
    mock_llm = MockLLMProvider()

    # Turn 1:
    mock_llm.add_response(LLMResponse(text="Your balance is ₹5,000.", finish_reason="stop"))
    # Turn 2:
    mock_llm.add_response(LLMResponse(text="Yes, you have enough funds to transfer ₹2,000.", finish_reason="stop"))

    orchestrator = AgentOrchestrator(
        llm_provider=mock_llm,
        session_manager=manager,
    )

    # Turn 1 Execution
    res1 = await orchestrator.run(
        session_id="sess_multi_turn",
        customer_id="cust_001",
        message="What is my balance?",
    )
    assert "₹5,000" in res1.response

    # Verify session in manager has turn 1 user + assistant messages
    saved_session = await manager.get_session("sess_multi_turn")
    assert len(saved_session.messages) == 2
    assert saved_session.messages[0]["content"] == "What is my balance?"
    assert saved_session.messages[1]["content"] == "Your balance is ₹5,000."

    # Turn 2 Execution (history is automatically loaded from manager)
    res2 = await orchestrator.run(
        session_id="sess_multi_turn",
        customer_id="cust_001",
        message="Can I transfer ₹2,000?",
    )
    assert "transfer ₹2,000" in res2.response

    # Verify mock_llm received full history for turn 2
    turn2_messages = mock_llm.call_history[1]["messages"]
    assert len(turn2_messages) == 3
    assert turn2_messages[0]["content"] == "What is my balance?"
    assert turn2_messages[1]["content"] == "Your balance is ₹5,000."
    assert turn2_messages[2]["content"] == "Can I transfer ₹2,000?"
