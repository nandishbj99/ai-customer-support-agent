from contextlib import asynccontextmanager
import pytest

from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.types import LLMResponse, ToolCall
from app.agent.orchestrator import AgentOrchestrator
from app.agent.tool_router import ToolRouter
from app.seeds.seed_data import det_uuid


@pytest.mark.asyncio
async def test_orchestrator_e2e_scenario_s01_insufficient_funds(db_session):
    """End-to-end integration test: Orchestrator executes real ToolRouter against S-01 seed data.
    
    Customer user_001 inquires about why txn_201 failed.
    The agent calls getTransaction, receives the INSUFFICIENT_FUNDS result, and answers the customer.
    """
    from app.tools.factory import ToolServiceFactory

    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    router = ToolRouter(services=services)
    txn_id = str(det_uuid(201))
    user_id = str(det_uuid(1))

    mock_llm = MockLLMProvider()

    # Step 1: Model inspects user message and requests getTransaction
    mock_llm.add_response(
        LLMResponse(
            tool_calls=[
                ToolCall(
                    id="call_tx_lookup",
                    name="getTransaction",
                    arguments={"txn_id": txn_id},
                )
            ],
            finish_reason="tool_call",
        )
    )

    # Step 2: Model formulates answer after receiving database observation
    mock_llm.add_response(
        LLMResponse(
            text="Your payment of ₹5,000.00 failed because of insufficient funds in your linked account.",
            finish_reason="stop",
        )
    )

    orchestrator = AgentOrchestrator(llm_provider=mock_llm, tool_router=router)

    result = await orchestrator.run(
        session_id="session_test_s01",
        customer_id=user_id,
        message="Why did my last transaction fail?",
    )

    assert result.status == "success"
    assert result.escalated is False
    assert result.tool_calls_made == ["getTransaction"]
    assert result.iterations == 2
    assert "insufficient funds" in result.response.lower()

    # Verify history in mock LLM provider has both user question, tool call, and tool result
    assert len(mock_llm.call_history) == 2
    second_call_messages = mock_llm.call_history[1]["messages"]
    tool_msg = [m for m in second_call_messages if m.get("role") == "tool"][0]
    assert tool_msg["content"]["success"] is True
    assert tool_msg["content"]["data"]["failure_reason"] == "INSUFFICIENT_FUNDS"
    assert tool_msg["content"]["data"]["amount_inr"] == 5000.0
