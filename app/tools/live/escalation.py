from app.tools.base import EscalationServiceBase
from app.tools.schemas import ToolResult


class LiveEscalationService(EscalationServiceBase):
    """Production live adapter delegating to HITL Celery Queue."""

    async def escalate_to_human_agent(
        self,
        user_id: str,
        reason: str,
        conversation_summary: str,
        priority: str = "medium",
    ) -> ToolResult:
        raise NotImplementedError("Live HITL queue escalation not configured.")
