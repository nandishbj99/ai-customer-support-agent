import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

from app.security.pii import redact_pii
from app.security.rate_limiter import rate_limiter

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects strict HTTP security headers (CSP, HSTS, X-Frame-Options, etc.) to harden against web attacks."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Enforces global IP-based and token-based rate limits."""

    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Don't rate limit health checks
        if request.url.path in ("/health", "/healthz"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        # Combine IP and authorization header prefix for user-specific bucket if present
        auth_header = request.headers.get("Authorization", "")
        rate_key = f"rl_{client_ip}_{auth_header[:16]}"

        allowed, retry_after = rate_limiter.is_allowed(
            rate_key,
            limit=self.requests_per_minute,
            window_seconds=60,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests and outgoing responses with latency and PII redaction."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        path = request.url.path
        method = request.method

        response: Response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        if path not in ("/health", "/healthz"):
            logger.info(
                "http_request_finished",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        return response
