import pytest

from app.agent.tool_router import ToolRouter
from app.rag.embeddings.mock import MockEmbeddingProvider
from app.rag.knowledge import PolicyKnowledgeService
from app.rag.store import VectorKnowledgeStore
from app.tools.factory import ToolServiceFactory
from app.tools.mock.policy import MockPolicyService


@pytest.mark.asyncio
async def test_mock_policy_service_direct():
    provider = MockEmbeddingProvider()
    store = VectorKnowledgeStore()
    knowledge = PolicyKnowledgeService(vector_store=store, embedding_provider=provider)
    policy_service = MockPolicyService(knowledge_service=knowledge)

    result = await policy_service.search_policy(query="What is the refund timeline?", top_k=2)
    assert result.success is True
    assert result.data is not None
    assert result.data["total_found"] >= 1
    assert "matches" in result.data
    first_match = result.data["matches"][0]
    assert "title" in first_match
    assert "snippet" in first_match


@pytest.mark.asyncio
async def test_tool_router_dispatches_search_policy(db_session):
    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    router = ToolRouter(services=services)

    result = await router.execute(
        tool_name="searchPolicy",
        arguments={"query": "unauthorized electronic transaction liability"},
        session_user_id="user_test_001",
    )

    assert result.success is True
    assert result.data["query"] == "unauthorized electronic transaction liability"
    assert "matches" in result.data
    assert len(result.data["matches"]) >= 1
