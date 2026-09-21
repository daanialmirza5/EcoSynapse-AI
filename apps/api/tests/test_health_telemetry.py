import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_telemetry():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "telemetry" in data
    assert "uptime_seconds" in data["telemetry"]
    assert isinstance(data["telemetry"]["uptime_seconds"], (int, float))
    assert data["telemetry"]["uptime_seconds"] >= 0
    assert data["telemetry"]["system"] == "operational"
