import uuid
from datetime import datetime, timezone
import structlog

from app.tools.base import NotificationServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult

logger = structlog.get_logger()


class MockNotificationService(NotificationServiceBase):
    """Mock implementation of NotificationServiceBase that records structured logs."""

    async def send_notification(
        self,
        user_id: str,
        channel: str,
        message: str,
    ) -> ToolResult:
        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        valid_channels = {"sms", "email", "push", "in_app"}
        clean_channel = channel.lower().strip()
        if clean_channel not in valid_channels:
            return ToolResult.fail(
                "INVALID_CHANNEL",
                f"Unsupported notification channel '{channel}'. Supported: {', '.join(sorted(valid_channels))}",
            )

        notification_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # In mock mode, log output as structured event
        logger.info(
            "mock_notification_sent",
            notification_id=notification_id,
            user_id=user_id,
            channel=clean_channel,
            message_length=len(message),
        )

        return ToolResult.ok(
            {
                "notification_id": notification_id,
                "user_id": str(parsed_user_id),
                "channel": clean_channel,
                "status": "delivered_mock",
                "message": message,
                "timestamp": now_iso,
            }
        )
