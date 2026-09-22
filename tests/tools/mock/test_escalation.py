import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.escalation import MockEscalationService


@pytest.mark.asyncio
async def test_escalate_to_human_agent_high_priority():
    service = MockEscalationService()
    res = await service.escalate_to_human_agent(
        user_id=str(det_uuid(2)),
        reason="Repeated suspected fraud block on legitimate transaction.",
        conversation_summary="Customer attempted transfer of ₹25,000 which was blocked.",
        priority="high",
    )
    assert res.success is True
    assert res.data["status"] == "queued_for_human_agent"
    assert res.data["priority"] == "high"
    assert res.data["estimated_wait_time_minutes"] == 5
    assert "specialist" in res.data["message"]


@pytest.mark.asyncio
async def test_escalate_to_human_agent_medium_priority():
    service = MockEscalationService()
    res = await service.escalate_to_human_agent(
        user_id=str(det_uuid(1)),
        reason="Customer needs personalized fee waiver explanation.",
        conversation_summary="General inquiry regarding late payment charges.",
        priority="medium",
    )
    assert res.success is True
    assert res.data["priority"] == "medium"
    assert res.data["estimated_wait_time_minutes"] == 15
