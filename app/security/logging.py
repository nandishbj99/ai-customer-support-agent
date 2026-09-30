from typing import Any, Dict
import structlog
from app.security.pii import redact_pii


def structlog_pii_masking_processor(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Custom structlog processor that scrubs all PII and credentials from log event payloads."""
    # Redact message string and any extra keyword arguments
    return redact_pii(event_dict)
