import httpx
import pytest

from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.types import LLMResponse
from app.agent.orchestrator import AgentOrchestrator
from app.api.v1.chat import get_orchestrator
from app.main import app


@pytest.mark.asyncio
async def test_chat_message_endpoint():
    mock_llm = MockLLMProvider()
    mock_llm.add_response(
        LLMResponse(
            text="Your account is active and in good standing.",
            finish_reason="stop",
        )
    )
    test_orchestrator = AgentOrchestrator(llm_provider=mock_llm)

    app.dependency_overrides[get_orchestrator] = lambda: test_orchestrator

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/chat/message",
                json={
                    "session_id": "sess_api_test",
                    "customer_id": "cust_123",
                    "message": "Is my account active?",
                },
            )

            assert resp.status_code == 200
            data = resp.json()
            assert data["session_id"] == "sess_api_test"
            assert data["status"] == "success"
            assert "active and in good standing" in data["response"]
            assert data["confidence_score"] == 0.95
            assert data["escalated"] is False
    finally:
        app.dependency_overrides.clear()
