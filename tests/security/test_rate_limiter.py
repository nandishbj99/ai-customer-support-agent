import pytest
from app.security.rate_limiter import SlidingWindowRateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = SlidingWindowRateLimiter(default_limit_per_minute=5)
    key = "test_ip_1"

    for _ in range(5):
        allowed, retry_after = limiter.is_allowed(key, limit=5, window_seconds=60)
        assert allowed is True
        assert retry_after == 0


def test_rate_limiter_blocks_above_limit():
    limiter = SlidingWindowRateLimiter(default_limit_per_minute=3)
    key = "test_ip_2"

    # 3 allowed
    for _ in range(3):
        allowed, _ = limiter.is_allowed(key, limit=3, window_seconds=60)
        assert allowed is True

    # 4th blocked
    blocked, retry_after = limiter.is_allowed(key, limit=3, window_seconds=60)
    assert blocked is False
    assert retry_after > 0


def test_rate_limiter_reset():
    limiter = SlidingWindowRateLimiter(default_limit_per_minute=2)
    key = "test_ip_3"
    limiter.is_allowed(key, limit=2)
    limiter.is_allowed(key, limit=2)

    # Now blocked
    blocked, _ = limiter.is_allowed(key, limit=2)
    assert blocked is False

    # Reset
    limiter.reset(key)
    allowed_again, _ = limiter.is_allowed(key, limit=2)
    assert allowed_again is True
