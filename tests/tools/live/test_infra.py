import time
import pytest
import pybreaker

from app.tools.live.infra import (
    ClientAPIError,
    SimpleTTLCache,
    TransientNetworkError,
    create_circuit_breaker,
    with_resilience,
)
from app.tools.schemas import ToolResult


@pytest.mark.asyncio
async def test_tc26_circuit_breaker_opens_after_failures():
    """TC-26: Circuit breaker opens after 5 failures and returns SERVICE_UNAVAILABLE."""
    breaker = create_circuit_breaker(name="TestRazorpay", fail_max=5, reset_timeout=60)

    @with_resilience(breaker=breaker, max_retries=1)
    async def failing_api_call():
        raise TransientNetworkError("500 Internal Server Error from Gateway")

    # Trigger 5 failures to open the circuit breaker
    for _ in range(5):
        res = await failing_api_call()
        assert res.success is False

    # 6th call: circuit breaker is open
    res_open = await failing_api_call()
    assert res_open.success is False
    assert res_open.error.code == "SERVICE_UNAVAILABLE"
    assert "Circuit is open" in res_open.error.message


@pytest.mark.asyncio
async def test_tc27_circuit_breaker_resets_after_timeout():
    """TC-27: Circuit breaker resets after reset_timeout expires and allows calls."""
    # Use 1 second reset timeout for fast test execution
    breaker = create_circuit_breaker(name="TestFastBreaker", fail_max=2, reset_timeout=1)

    fail = True

    @with_resilience(breaker=breaker, max_retries=1)
    async def dynamic_api_call():
        if fail:
            raise TransientNetworkError("Down")
        return ToolResult.ok({"status": "recovered"})

    # Fail twice to trip circuit
    await dynamic_api_call()
    await dynamic_api_call()
    res_tripped = await dynamic_api_call()
    assert res_tripped.error.code == "SERVICE_UNAVAILABLE"

    # Wait for timeout to reset
    time.sleep(1.1)
    fail = False

    # Breaker should allow call in half-open state and recover
    res_recovered = await dynamic_api_call()
    assert res_recovered.success is True
    assert res_recovered.data["status"] == "recovered"


@pytest.mark.asyncio
async def test_tc28_retry_on_transient_error():
    """TC-28: Retry with backoff succeeds when transient error resolves on retry."""
    breaker = create_circuit_breaker(name="TestRetry", fail_max=10, reset_timeout=60)
    attempts = 0

    @with_resilience(breaker=breaker, max_retries=3)
    async def flappy_api_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TransientNetworkError("Transient 503 Service Unavailable")
        return ToolResult.ok({"attempt": attempts})

    res = await flappy_api_call()
    assert res.success is True
    assert attempts == 3
    assert res.data["attempt"] == 3


@pytest.mark.asyncio
async def test_tc29_no_retry_on_client_error():
    """TC-29: 4xx ClientAPIError fails immediately without retrying."""
    breaker = create_circuit_breaker(name="TestNoRetry", fail_max=10, reset_timeout=60)
    attempts = 0

    @with_resilience(breaker=breaker, max_retries=3)
    async def client_error_call():
        nonlocal attempts
        attempts += 1
        raise ClientAPIError("400 Bad Request: Invalid account number")

    res = await client_error_call()
    assert res.success is False
    assert res.error.code == "EXTERNAL_CLIENT_ERROR"
    # Verify it was only called once (no retries)
    assert attempts == 1


def test_tc30_response_ttl_cache():
    """TC-30: Response cache returns cached value within TTL and evicts when expired."""
    cache = SimpleTTLCache(default_ttl_seconds=1)

    cache.set("acc_123", {"balance_inr": 5000.0})
    # Immediate fetch succeeds
    assert cache.get("acc_123") == {"balance_inr": 5000.0}

    # Wait for 1.1s to expire TTL
    time.sleep(1.1)
    assert cache.get("acc_123") is None
