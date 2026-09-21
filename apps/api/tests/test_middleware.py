import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from app.core.middleware import SecurityHeadersMiddleware, InMemoryRateLimiter, RateLimitMiddleware


def homepage(request):
    return PlainTextResponse("OK")


def test_security_headers_middleware():
    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(SecurityHeadersMiddleware)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_in_memory_rate_limiter():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10.0)
    
    allowed, remaining, _ = limiter.is_allowed("127.0.0.1")
    assert allowed is True
    assert remaining == 1

    allowed, remaining, _ = limiter.is_allowed("127.0.0.1")
    assert allowed is True
    assert remaining == 0

    allowed, remaining, retry_after = limiter.is_allowed("127.0.0.1")
    assert allowed is False
    assert retry_after > 0


def test_rate_limit_middleware():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10.0)
    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(RateLimitMiddleware, limiter=limiter)
    client = TestClient(app)

    res1 = client.get("/")
    assert res1.status_code == 200
    assert res1.headers["X-RateLimit-Remaining"] == "1"

    res2 = client.get("/")
    assert res2.status_code == 200
    assert res2.headers["X-RateLimit-Remaining"] == "0"

    res3 = client.get("/")
    assert res3.status_code == 429
    assert "Retry-After" in res3.headers
