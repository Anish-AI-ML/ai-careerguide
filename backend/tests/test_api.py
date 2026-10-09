from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BODY = {"education": {"branch": "Computer Science", "cgpa": 8.5},
        "skills": ["Python", "ML", "TensorFlow"], "interests": ["Artificial Intelligence"],
        "career_goal": "AI/ML Engineer"}

def test_health_and_careers():
    assert client.get("/api/health").json() == {"status": "ok"}
    assert len(client.get("/api/careers").json()) == 11

def test_career_404_uses_error_format():
    r = client.get("/api/careers/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "http_error"

def test_analyze_ok():
    r = client.post("/api/career/analyze", json=BODY)
    assert r.status_code == 200
    d = r.json()
    assert d["top"]["career"] == "AI/ML Engineer" and len(d["alternatives"]) == 4
    assert abs(sum(d["weights_used"].values()) - 1) < 1e-9

def test_validation_error():
    r = client.post("/api/career/analyze", json={"education": {"cgpa": 14}})
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "education.cgpa"

def test_bad_weights_422():
    r = client.post("/api/career/analyze", json={**BODY, "weights": {"skills": -1}})
    assert r.status_code == 422


def test_ai_endpoints_are_rate_limited(monkeypatch):
    monkeypatch.setenv("AI_RATE_LIMIT_PER_MIN", "0")
    r = client.post("/api/career/analyze", json=BODY)
    assert r.status_code == 429 and r.json()["error"]["code"] == "http_error"
