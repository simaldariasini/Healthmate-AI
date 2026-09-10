from fastapi.testclient import TestClient

from app.main import app

def test_only_approved_knowledge_is_returned():
    with TestClient(app) as client:
        conditions = client.get("/api/conditions").json()
        diabetes = next(item for item in conditions if item["slug"] == "diabetes")
        response = client.get(f"/api/conditions/{diabetes['id']}/knowledge")
    assert response.status_code == 200
    assert response.json()["entries"]
    assert all(item["review_status"] == "approved" for item in response.json()["entries"])

def test_sources_are_attributed():
    with TestClient(app) as client:
        conditions = client.get("/api/conditions").json()
        response = client.get(f"/api/conditions/{conditions[0]['id']}/knowledge")
    payload = response.json()
    assert payload["sources"]
    assert all(source["url"].startswith("https://") for source in payload["sources"])

def test_assistant_falls_back_without_verified_knowledge():
    with TestClient(app) as client:
        response = client.post("/api/assistant/preview", json={"condition_ids": [99999], "question": "What should I eat?"})
    assert response.status_code == 200
    assert response.json()["needs_professional_guidance"] is True

def test_general_fibre_question_uses_approved_knowledge_without_conditions():
    with TestClient(app) as client:
        response = client.post("/api/assistant/preview", json={"condition_ids": [], "question": "What is fibre?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["sources"]
    assert "fibre" in payload["message"].lower() or "fiber" in payload["message"].lower()
