from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

def account(client):
 email=f"test-{uuid4().hex}@example.com"
 response=client.post("/api/auth/signup",json={"email":email,"password":"safe-password-123","name":"Test User"})
 assert response.status_code==200

def test_authentication_and_user_isolation():
 with TestClient(app) as first, TestClient(app) as second:
  account(first); account(second)
  created=first.post("/api/reminders",json={"title":"First user's reminder","time":"09:00"})
  assert created.status_code==200
  assert all(r["title"]!="First user's reminder" for r in second.get("/api/reminders").json())

def test_weekly_plan_and_shopping_list():
 with TestClient(app) as client:
  account(client)
  plan=client.post("/api/meal-plans/generate",json={}).json()
  assert len(plan["items"])==28
  shopping=client.post(f"/api/shopping-list/regenerate/{plan['id']}")
  assert shopping.status_code==200 and shopping.json()

def test_meal_completion_is_saved_in_progress_summary():
 with TestClient(app) as client:
  account(client)
  plan=client.post("/api/meal-plans/generate",json={}).json()
  item=plan["items"][0]
  response=client.patch(f"/api/meal-plans/items/{item['id']}/completion",json={"completed":True})
  assert response.status_code==200 and response.json()["completed"] is True
  summary=client.get("/api/progress/summary").json()
  assert summary["meals_completed"] >= 1

def test_question_influences_approved_retrieval():
 with TestClient(app) as client:
  conditions=client.get("/api/conditions").json(); diabetes=next(c for c in conditions if c["slug"]=="diabetes")
  answer=client.post("/api/assistant/preview",json={"condition_ids":[diabetes["id"]],"question":"How can I include more fiber?"})
  assert answer.status_code==200
  assert answer.json()["sources"]
