from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tools.live.account import CoreBankingAccountService
from app.tools.live.escalation import LiveEscalationService
from app.tools.live.fraud import FraudDetectionMLService
from app.tools.live.notification import TwilioNotificationService
from app.tools.live.payment import RazorpayPaymentService
from app.tools.live.refund import RazorpayRefundService
from app.tools.live.ticket import FreshdeskTicketService
from app.tools.live.transaction import RazorpayTransactionService
from app.tools.mock.account import MockAccountService
from app.tools.mock.escalation import MockEscalationService
from app.tools.mock.fraud import MockFraudService
from app.tools.mock.notification import MockNotificationService
from app.tools.mock.payment import MockPaymentService
from app.tools.mock.refund import MockRefundService
from app.tools.mock.ticket import MockTicketService
from app.tools.mock.transaction import MockTransactionService


class ToolServiceFactory:
    """Factory creating concrete tool adapters based on TOOL_MODE (mock, live, hybrid)."""

    @classmethod
    def get_tool_mode(cls, tool_domain: str, global_mode: str, overrides: Optional[Dict[str, str]] = None) -> str:
        """Resolve effective mode for a given tool domain (e.g. 'transaction')."""
        if overrides and tool_domain in overrides:
            return overrides[tool_domain].lower()
        if global_mode.lower() == "hybrid":
            # In hybrid mode, specific tools can be live while others remain mock
            # Default to mock unless explicit override is provided
            return "mock"
        return global_mode.lower()

    @classmethod
    def create_services(
        cls,
        mode: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
        overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Instantiate and return the suite of tool adapters."""
        active_mode = (mode or settings.TOOL_MODE).lower()

        services: Dict[str, Any] = {}

        # 1. Transaction Service
        m = cls.get_tool_mode("transaction", active_mode, overrides)
        if m == "live":
            services["transaction"] = RazorpayTransactionService(
                key_id=settings.RAZORPAY_KEY_ID,
                key_secret=settings.RAZORPAY_KEY_SECRET,
            )
        else:
            services["transaction"] = MockTransactionService(db_session)

        # 2. Account Service
        m = cls.get_tool_mode("account", active_mode, overrides)
        if m == "live":
            services["account"] = CoreBankingAccountService(
                api_url=settings.CORE_BANKING_API_URL,
                api_key=settings.CORE_BANKING_API_KEY,
            )
        else:
            services["account"] = MockAccountService(db_session)

        # 3. Payment Service
        m = cls.get_tool_mode("payment", active_mode, overrides)
        if m == "live":
            services["payment"] = RazorpayPaymentService(
                key_id=settings.RAZORPAY_KEY_ID,
                key_secret=settings.RAZORPAY_KEY_SECRET,
            )
        else:
            services["payment"] = MockPaymentService(db_session)

        # 4. Fraud Service
        m = cls.get_tool_mode("fraud", active_mode, overrides)
        if m == "live":
            services["fraud"] = FraudDetectionMLService()
        else:
            services["fraud"] = MockFraudService(db_session)

        # 5. Refund Service
        m = cls.get_tool_mode("refund", active_mode, overrides)
        if m == "live":
            services["refund"] = RazorpayRefundService(
                key_id=settings.RAZORPAY_KEY_ID,
                key_secret=settings.RAZORPAY_KEY_SECRET,
            )
        else:
            services["refund"] = MockRefundService(db_session)

        # 6. Ticket Service
        m = cls.get_tool_mode("ticket", active_mode, overrides)
        if m == "live":
            services["ticket"] = FreshdeskTicketService(
                domain=settings.FRESHDESK_DOMAIN,
                api_key=settings.FRESHDESK_API_KEY,
            )
        else:
            services["ticket"] = MockTicketService(db_session)

        # 7. Notification Service
        m = cls.get_tool_mode("notification", active_mode, overrides)
        if m == "live":
            services["notification"] = TwilioNotificationService(
                account_sid=settings.TWILIO_ACCOUNT_SID,
                auth_token=settings.TWILIO_AUTH_TOKEN,
                from_phone=settings.TWILIO_PHONE_NUMBER,
            )
        else:
            services["notification"] = MockNotificationService()

        # 8. Escalation Service
        m = cls.get_tool_mode("escalation", active_mode, overrides)
        if m == "live":
            services["escalation"] = LiveEscalationService()
        else:
            services["escalation"] = MockEscalationService()

        return services
