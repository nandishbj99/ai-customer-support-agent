from app.tools.base import NotificationServiceBase
from app.tools.schemas import ToolResult


class TwilioNotificationService(NotificationServiceBase):
    """Production live adapter integrating with Twilio SMS / AWS SES Email."""

    def __init__(self, account_sid: str = "", auth_token: str = "", from_phone: str = ""):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone

    async def send_notification(
        self,
        user_id: str,
        channel: str,
        message: str,
    ) -> ToolResult:
        raise NotImplementedError("Twilio live notification service not configured.")
