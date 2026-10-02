from fastapi.testclient import TestClient

from app.graph.workflow import get_workflow
from app.main import app


def test_api_chat_approval_and_session_persistence():
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "My order ORD1002 was delivered 37 days ago and I want a refund."})
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "human_review_required"
        assert payload["policy_sources"]
        session = client.get(f"/api/sessions/{payload['session_id']}")
        assert session.status_code == 200
        approved = client.post(f"/api/approval/{payload['workflow_id']}", json={"decision": "approve"})
        assert approved.status_code == 200
        assert approved.json()["completed_actions"][0]["success"] is True
        assert "does not issue funds" in approved.json()["recommended_action"]["expected_impact"]


def test_api_validation_health_and_file_upload():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.post("/api/chat", json={"message": "x"}).status_code == 422
        assert client.post("/api/documents/upload", files={"file": ("bad.pdf", b"not a pdf", "application/pdf")}).status_code == 415


def test_approval_recovers_after_checkpoint_store_is_recreated():
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "My order ORD1002 was delivered 37 days ago and I want a refund."})
        workflow_id = response.json()["workflow_id"]
        get_workflow.cache_clear()
        approved = client.post(f"/api/approval/{workflow_id}", json={"decision": "approve"})
        assert approved.status_code == 200
        assert approved.json()["completed_actions"][0]["success"] is True