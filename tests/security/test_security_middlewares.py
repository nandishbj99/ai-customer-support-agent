import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.security.middleware import RateLimitingMiddleware, SecurityHeadersMiddleware
from app.security.rate_limiter import rate_limiter


@pytest.mark.asyncio
async def test_security_headers_present_on_endpoints():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        headers = resp.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert headers.get("Strict-Transport-Security") is not None
        assert "default-src 'self'" in headers.get("Content-Security-Policy", "")


def test_rate_limiting_middleware_burst():
    test_app = FastAPI()
    test_app.add_middleware(RateLimitingMiddleware, requests_per_minute=2)

    @test_app.get("/limited")
    def limited_endpoint():
        return {"ok": True}

    rate_limiter.reset()
    client = TestClient(test_app)

    # First 2 succeed
    r1 = client.get("/limited")
    assert r1.status_code == 200
    r2 = client.get("/limited")
    assert r2.status_code == 200

    # 3rd is rate limited
    r3 = client.get("/limited")
    assert r3.status_code == 429
    assert r3.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in r3.headers
