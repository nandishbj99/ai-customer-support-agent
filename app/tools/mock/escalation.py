import uuid
from datetime import datetime, timezone
import structlog

from app.tools.base import EscalationServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult

logger = structlog.get_logger()


class MockEscalationService(EscalationServiceBase):
    """Mock implementation of EscalationServiceBase (delegates to HITL queue)."""

    async def escalate_to_human_agent(
        self,
        user_id: str,
        reason: str,
        conversation_summary: str,
        priority: str = "medium",
    ) -> ToolResult:
        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        valid_priorities = {"low", "medium", "high", "urgent"}
        clean_priority = priority.lower().strip()
        if clean_priority not in valid_priorities:
            clean_priority = "medium"

        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        logger.info(
            "mock_human_escalation_enqueued",
            escalation_id=escalation_id,
            user_id=user_id,
            priority=clean_priority,
            reason=reason,
        )

        return ToolResult.ok(
            {
                "escalation_id": escalation_id,
                "user_id": str(parsed_user_id),
                "status": "queued_for_human_agent",
                "priority": clean_priority,
                "reason": reason,
                "conversation_summary": conversation_summary,
                "estimated_wait_time_minutes": 5 if clean_priority in ("high", "urgent") else 15,
                "message": "Your conversation has been routed to a human specialist. A representative will connect shortly.",
                "timestamp": now_iso,
            }
        )
