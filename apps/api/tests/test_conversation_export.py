from fastapi.testclient import TestClient
from app.main import app


def test_conversation_export_json_and_markdown(client: TestClient):
    # 1. Create a conversation
    create_res = client.post("/api/v1/conversations", json={"title": "Soil Remediation Study", "session_id": "test-session-123"})
    assert create_res.status_code == 201
    conv_id = create_res.json()["id"]

    # 2. Add a message
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "We need biochar intervention for heavy metal soil."},
    )
    assert msg_res.status_code == 200

    # 3. Export as JSON
    json_export = client.get(f"/api/v1/conversations/{conv_id}/export?format=json")
    assert json_export.status_code == 200
    export_data = json_export.json()
    assert export_data["format"] == "json"
    assert export_data["conversation"]["id"] == conv_id
    assert len(export_data["conversation"]["messages"]) >= 1

    # 4. Export as Markdown
    md_export = client.get(f"/api/v1/conversations/{conv_id}/export?format=markdown")
    assert md_export.status_code == 200
    md_data = md_export.json()
    assert md_data["format"] == "markdown"
    assert "# Conversation Export: Soil Remediation Study" in md_data["content"]
