import pytest
from fastapi.testclient import TestClient


def test_sql_injection_resilience(client: TestClient):
    # Test SQL injection string in conversation creation
    payload = {
        "title": "'; DROP TABLE conversations; --",
        "session_id": "test-session-sqli",
    }
    res = client.post("/api/v1/conversations", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "'; DROP TABLE conversations; --"

    # Verify tables still exist
    list_res = client.get("/api/v1/conversations")
    assert list_res.status_code == 200


def test_nonexistent_ids_return_404(client: TestClient):
    res = client.get("/api/v1/conversations/non-existent-uuid-99999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

    res_export = client.get("/api/v1/conversations/non-existent-uuid-99999/export")
    assert res_export.status_code == 404


def test_unicode_and_special_characters_in_messages(client: TestClient):
    conv_res = client.post("/api/v1/conversations", json={"title": "Unicode Test 🌲"})
    assert conv_res.status_code == 201
    cid = conv_res.json()["id"]

    complex_text = "Testing multilingual: 🌲 🌳 🌾 🌿 \n\t\r Zero-width \u200b\u200c\u200d Arabic: تجربة"
    msg_res = client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"content": complex_text},
    )
    assert msg_res.status_code == 200
    assert msg_res.json()["assistant_message"]["content"] is not None
