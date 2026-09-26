import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.types import LLMResponse, ToolCall
from app.agent.orchestrator import AgentOrchestrator, AgentResult
from app.agent.tool_router import ToolRouter
from app.tools.schemas import ToolResult


@pytest.mark.asyncio
async def test_orchestrator_direct_answer():
    mock_llm = MockLLMProvider()
    mock_llm.add_response(
        LLMResponse(
            text="Hello! How can I help you today with your banking queries?",
            finish_reason="stop",
        )
    )

    orchestrator = AgentOrchestrator(llm_provider=mock_llm)
    result = await orchestrator.run(
        session_id="sess_123",
        customer_id="user_001",
        message="Hi",
    )

    assert isinstance(result, AgentResult)
    assert result.status == "success"
    assert "banking queries" in result.response
    assert not result.escalated
    assert result.tool_calls_made == []
    assert result.iterations == 1


@pytest.mark.asyncio
async def test_orchestrator_react_with_tool_call():
    mock_llm = MockLLMProvider()

    # Step 1: Model calls getAccountBalance
    mock_llm.add_response(
        LLMResponse(
            tool_calls=[ToolCall(id="c1", name="getAccountBalance", arguments={"account_id": "acc_001"})],
            finish_reason="tool_call",
        )
    )
    # Step 2: Model answers using tool observation
    mock_llm.add_response(
        LLMResponse(
            text="Your current available balance is ₹2,500.00.",
            finish_reason="stop",
        )
    )

    # Mock tool router
    mock_router = MagicMock(spec=ToolRouter)
    mock_router.execute = AsyncMock(
        return_value=ToolResult.ok({
            "account_id": "acc_001",
            "balance_inr": 2500.0,
            "currency": "INR",
        })
    )

    orchestrator = AgentOrchestrator(llm_provider=mock_llm, tool_router=mock_router)
    result = await orchestrator.run(
        session_id="sess_123",
        customer_id="user_001",
        message="What is my balance?",
    )

    assert result.status == "success"
    assert "₹2,500.00" in result.response
    assert result.tool_calls_made == ["getAccountBalance"]
    assert result.iterations == 2
    mock_router.execute.assert_called_once_with(
        tool_name="getAccountBalance",
        arguments={"account_id": "acc_001"},
        session_user_id="user_001",
        session_id="sess_123",
    )


@pytest.mark.asyncio
async def test_orchestrator_escalation_detection():
    mock_llm = MockLLMProvider()
    mock_llm.add_response(
        LLMResponse(
            tool_calls=[
                ToolCall(
                    id="c1",
                    name="escalateToHumanAgent",
                    arguments={"reason": "Customer suspected unauthorized transaction", "priority": "high"},
                )
            ],
            finish_reason="tool_call",
        )
    )
    mock_llm.add_response(
        LLMResponse(
            text="I have escalated your unauthorized transaction dispute to our fraud response team.",
            finish_reason="stop",
        )
    )

    mock_router = MagicMock(spec=ToolRouter)
    mock_router.execute = AsyncMock(
        return_value=ToolResult.ok({
            "escalation_id": "esc_123",
            "status": "QUEUED",
        })
    )

    orchestrator = AgentOrchestrator(llm_provider=mock_llm, tool_router=mock_router)
    result = await orchestrator.run(
        session_id="sess_123",
        customer_id="user_001",
        message="Someone made an unauthorized charge on my card!",
    )

    assert result.status == "escalated"
    assert result.escalated is True
    assert "escalated" in result.response


@pytest.mark.asyncio
async def test_orchestrator_max_iterations_exhausted():
    mock_llm = MockLLMProvider()
    # Loop continuously requests tools beyond max_iterations (3)
    for _ in range(5):
        mock_llm.add_response(
            LLMResponse(
                tool_calls=[ToolCall(id="c", name="getTransaction", arguments={"transaction_id": "tx_1"})],
                finish_reason="tool_call",
            )
        )

    mock_router = MagicMock(spec=ToolRouter)
    mock_router.execute = AsyncMock(return_value=ToolResult.ok({"status": "SUCCESS"}))

    orchestrator = AgentOrchestrator(
        llm_provider=mock_llm,
        tool_router=mock_router,
        max_iterations=3,
    )
    result = await orchestrator.run(
        session_id="sess_123",
        customer_id="user_001",
        message="Check my transaction again",
    )

    assert result.status == "fallback"
    assert result.escalated is True
    assert result.iterations == 3


@pytest.mark.asyncio
async def test_orchestrator_timeout_fallback():
    mock_llm = MockLLMProvider()

    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(0.1)
        return LLMResponse(text="Done")

    mock_llm.generate = slow_generate

    orchestrator = AgentOrchestrator(
        llm_provider=mock_llm,
        timeout_seconds=0.01,  # Short timeout
    )
    result = await orchestrator.run(
        session_id="sess_123",
        customer_id="user_001",
        message="Check something",
    )

    assert result.status == "fallback"
    assert result.escalated is True
    assert "experiencing a slight delay" in result.response


@pytest.mark.asyncio
async def test_orchestrator_exception_fallback():
    mock_llm = MockLLMProvider()

    async def failing_generate(*args, **kwargs):
        raise RuntimeError("API connection failure")

    mock_llm.generate = failing_generate

    orchestrator = AgentOrchestrator(llm_provider=mock_llm)
    result = await orchestrator.run(
        session_id="sess_123",
        customer_id="user_001",
        message="Check something",
    )

    assert result.status == "error"
    assert result.escalated is True
    assert "unexpected issue" in result.response
