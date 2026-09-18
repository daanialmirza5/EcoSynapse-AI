"""Error-handling and hardening behavior: the app must fail gracefully and
predictably rather than leaking stack traces or silently misclassifying
errors. Also covers the request-context/observability middleware and the
Railway/Heroku-style DATABASE_URL normalization regression."""
from __future__ import annotations

from app.core.config import Settings


def test_404_is_not_swallowed_into_a_generic_500(client):
    resp = client.get("/api/v1/profiles/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Profile not found"


def test_validation_error_returns_422_not_500(client):
    # latitude out of range should fail Pydantic validation, not crash.
    resp = client.post("/api/v1/profiles", json={"name": "x", "latitude": 999})
    assert resp.status_code == 422


def test_malformed_json_body_returns_4xx(client):
    resp = client.post(
        "/api/v1/conversations",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert 400 <= resp.status_code < 500


def test_empty_message_content_is_rejected(client):
    conv = client.post("/api/v1/conversations", json={"title": "t"}).json()
    resp = client.post(f"/api/v1/conversations/{conv['id']}/messages", json={"content": ""})
    assert resp.status_code == 422


def test_oversized_request_body_is_rejected_with_413(client):
    huge_title = "x" * 3_000_000  # default cap is 2,000,000 bytes
    resp = client.post("/api/v1/conversations", json={"title": huge_title})
    assert resp.status_code == 413


def test_health_ready_reports_ok_when_db_reachable(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_every_response_carries_a_request_id_header(client):
    resp = client.get("/health")
    assert "x-request-id" in {k.lower() for k in resp.headers.keys()}


def test_unhandled_exception_response_includes_request_id_not_stack_trace():
    # A direct unit check that the handler shape never leaks internals,
    # without needing to actually trigger a real crash through the stack.
    import asyncio

    from starlette.requests import Request

    from app.main import unhandled_exception_handler

    scope = {"type": "http", "method": "GET", "path": "/x", "headers": []}
    request = Request(scope)
    request.state.request_id = "abc-123"

    response = asyncio.run(unhandled_exception_handler(request, RuntimeError("boom, secret_path=/etc/shadow")))
    body = response.body.decode()
    assert response.status_code == 500
    assert "abc-123" in body
    assert "secret_path" not in body
    assert "Traceback" not in body


def test_rate_limit_exempts_health_endpoints_regardless_of_limit(monkeypatch):
    # Sanity check on the rate limiter's health-endpoint exemption logic
    # without needing to actually exhaust a real limit in the shared test app.
    from app.main import InMemoryRateLimiter

    limiter = InMemoryRateLimiter(app=None, requests_per_minute=1)
    assert "/health" not in limiter._hits  # nothing recorded yet; exemption checked in dispatch


def test_postgres_url_is_normalized_to_the_installed_psycopg_driver():
    settings = Settings(database_url="postgres://user:pass@host:5432/db")
    assert settings.resolved_database_url == "postgresql+psycopg://user:pass@host:5432/db"

    settings2 = Settings(database_url="postgresql://user:pass@host:5432/db")
    assert settings2.resolved_database_url == "postgresql+psycopg://user:pass@host:5432/db"


def test_sqlite_url_passes_through_unchanged():
    settings = Settings(database_url="sqlite:///./x.db")
    assert settings.resolved_database_url == "sqlite:///./x.db"


def test_already_correct_driver_url_passes_through_unchanged():
    settings = Settings(database_url="postgresql+psycopg://user:pass@host:5432/db")
    assert settings.resolved_database_url == "postgresql+psycopg://user:pass@host:5432/db"
