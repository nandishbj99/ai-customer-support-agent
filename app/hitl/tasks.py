import asyncio
from datetime import datetime, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.hitl.service import ApprovalService

logger = structlog.get_logger()


async def run_sla_escalation_check() -> int:
    """Scan and auto-escalate requests exceeding the 30-minute SLA window (FR-05)."""
    logger.info("running_sla_escalation_job")
    async with async_session_factory() as session:
        try:
            service = ApprovalService(db_session=session)
            count = await service.auto_escalate_expired_slas()
            await session.commit()
            logger.info("sla_escalation_job_completed", escalated_count=count)
            return count
        except Exception as e:
            await session.rollback()
            logger.error("sla_escalation_job_failed", error=str(e))
            raise


# Celery worker task declaration (optional / pluggable when celery worker is running)
try:
    from celery import shared_task

    @shared_task(name="app.hitl.tasks.monitor_approval_slas")
    def monitor_approval_slas():
        """Celery periodic task for monitoring approval SLAs."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(run_sla_escalation_check())

except ImportError:
    # Celery not installed; fallback to direct async execution
    monitor_approval_slas = None
