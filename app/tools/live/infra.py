import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
import pybreaker
import structlog
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.tools.schemas import ToolResult

logger = structlog.get_logger()


class TransientNetworkError(Exception):
    """Raised when an external API call experiences a 5xx status or network timeout."""
    pass


class ClientAPIError(Exception):
    """Raised when an external API call experiences a 4xx client error (do not retry)."""
    pass


def should_retry_exception(exc: BaseException) -> bool:
    """Retry on transient network errors or timeouts; do not retry on 4xx client errors."""
    if isinstance(exc, ClientAPIError):
        return False
    if isinstance(exc, (TransientNetworkError, TimeoutError, ConnectionError)):
        return True
    return False


def create_circuit_breaker(
    name: str,
    fail_max: int = 5,
    reset_timeout: int = 60,
    exclude: Optional[List[Type[Exception]]] = None,
) -> pybreaker.CircuitBreaker:
    """Create a configured pybreaker CircuitBreaker for a live external provider."""
    exclude_list = exclude if exclude is not None else [ClientAPIError]
    return pybreaker.CircuitBreaker(
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        name=name,
        exclude=exclude_list,
    )


def with_resilience(breaker: pybreaker.CircuitBreaker, max_retries: int = 3):
    """Decorator wrapping an async external API call with retry and circuit breaker."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> ToolResult:
            # Retry wrapper using tenacity around breaker.calling()
            @retry(
                retry=retry_if_exception(should_retry_exception),
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=0.1, min=0.1, max=1.0),
                reraise=True,
            )
            async def _attempt_call():
                with breaker.calling():
                    return await func(*args, **kwargs)

            try:
                return await _attempt_call()
            except pybreaker.CircuitBreakerError as e:
                logger.error("circuit_breaker_tripped", provider=breaker.name, error=str(e))
                return ToolResult.fail(
                    "SERVICE_UNAVAILABLE",
                    f"External provider '{breaker.name}' is currently unavailable due to repeated failures. Circuit is open.",
                    {"provider": breaker.name, "circuit_state": "open"},
                )
            except ClientAPIError as e:
                logger.warning("external_client_error", provider=breaker.name, error=str(e))
                return ToolResult.fail("EXTERNAL_CLIENT_ERROR", str(e))
            except Exception as e:
                logger.error("external_call_failed", provider=breaker.name, error=str(e))
                return ToolResult.fail(
                    "EXTERNAL_SERVICE_FAILURE",
                    f"Call to external provider '{breaker.name}' failed: {str(e)}",
                )

        return wrapper

    return decorator


class SimpleTTLCache:
    """In-memory TTL cache with support for time-based eviction."""

    def __init__(self, default_ttl_seconds: int = 30):
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = (value, time.time() + ttl)

    def clear(self) -> None:
        self._cache.clear()
