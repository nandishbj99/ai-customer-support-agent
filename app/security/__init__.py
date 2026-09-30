"""Security, Authentication, Authorization & Audit Logging Module (FEAT-005)."""
from app.security.audit import AuditService
from app.security.dependencies import (
    get_current_user,
    get_current_user_token,
    requires_role,
    verify_api_key,
)
from app.security.logging import structlog_pii_masking_processor
from app.security.middleware import (
    RateLimitingMiddleware,
    RequestResponseLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.security.pii import mask_aadhaar, mask_account_or_card, mask_pan, mask_pii_string, redact_pii
from app.security.prompt_guard import InjectionRiskLevel, PromptGuard, prompt_guard
from app.security.rate_limiter import SlidingWindowRateLimiter, rate_limiter
from app.security.roles import UserRole, has_role
from app.security.sanitizer import sanitize_input_text
from app.security.tokens import (
    InvalidTokenError,
    TokenError,
    TokenExpiredError,
    TokenManager,
    token_manager,
)

__all__ = [
    "UserRole",
    "has_role",
    "TokenManager",
    "token_manager",
    "TokenError",
    "TokenExpiredError",
    "InvalidTokenError",
    "redact_pii",
    "mask_aadhaar",
    "mask_pan",
    "mask_account_or_card",
    "mask_pii_string",
    "structlog_pii_masking_processor",
    "sanitize_input_text",
    "PromptGuard",
    "prompt_guard",
    "InjectionRiskLevel",
    "SlidingWindowRateLimiter",
    "rate_limiter",
    "AuditService",
    "get_current_user",
    "get_current_user_token",
    "requires_role",
    "verify_api_key",
    "SecurityHeadersMiddleware",
    "RateLimitingMiddleware",
    "RequestResponseLoggingMiddleware",
]
