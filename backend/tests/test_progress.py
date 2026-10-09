import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.progress import readiness

H = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731


def test_readiness_math_and_bounds():
    s, b = readiness(60, 50, 2, 1, 2)
    assert s == round(60 * .5 + 50 * .2 + 50 * .15 + 50 * .15) == 55
    assert b["portfolio"]["value"] == 50 and b["courses"]["weight"] == 15
    assert readiness(0, 0, 0, 0, 0)[0] == 0 and readiness(100, 100, 9, 3, 3)[0] == 100


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def setup_user(client):
    t = client.post("/api/auth/register", json={"full_name": "P T", "email": f"{uuid.uuid4().hex[:8]}@example.com", "password": "progress-pass-1"}).json()["access_token"]
    return t


def test_progress_flow(client):
    t = setup_user(client)
    assert client.get("/api/progress").status_code == 401
    assert client.get("/api/progress", headers=H(t)).status_code == 404  # no profile yet
    client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": ["Python", "ML"], "projects": ["Traffic model"],
                                      "certifications": ["DL Specialization"], "career_goal": "AI/ML Engineer"}, headers=H(t))
    p0 = client.get("/api/progress", headers=H(t)).json()
    assert p0["career"] == "AI/ML Engineer" and 0 < p0["readiness_score"] < 60 and p0["courses"]["tracked"] == 0 and p0["pending_skills"] == []
    assert len(p0["history"]) == 1
    assert client.get("/api/progress", headers=H(t)).json()["history"] == p0["history"]  # unchanged state adds no snapshot

    assert client.put("/api/progress/courses/not-a-course", json={"status": "completed"}, headers=H(t)).status_code == 404
    assert client.put("/api/progress/courses/pytorch-tutorials", json={"status": "bogus"}, headers=H(t)).status_code == 422
    p1 = client.put("/api/progress/courses/pytorch-tutorials", json={"status": "in_progress"}, headers=H(t)).json()
    assert p1["courses"]["in_progress"] == 1 and p1["pending_skills"] == []  # only completed courses add pending skills
    p2 = client.put("/api/progress/courses/pytorch-tutorials", json={"status": "completed"}, headers=H(t)).json()
    assert p2["courses"]["completion_percent"] == 100 and p2["pending_skills"] == ["pytorch"]
    assert p2["readiness_score"] > p1["readiness_score"] and p2["courses"]["items"][0]["completed_at"]
    assert client.get("/api/progress/courses", headers=H(t)).json() == {"pytorch-tutorials": "completed"}

    p3 = client.post("/api/progress/apply-skills", json={}, headers=H(t)).json()
    assert p3["pending_skills"] == [] and "pytorch" in p3["skills"]["core_have"] and p3["skills"]["total_skills"] == p2["skills"]["total_skills"] + 1
    assert "PyTorch" in client.get("/api/profile", headers=H(t)).json()["skills"]
    assert p3["skills"]["coverage_percent"] > p2["skills"]["coverage_percent"]
    assert len(p3["history"]) == 3 and p3["history"][-1]["readiness"] == p3["readiness_score"]

    p4 = client.put("/api/progress/courses/pytorch-tutorials", json={"status": "none"}, headers=H(t)).json()
    assert p4["courses"]["tracked"] == 0


def test_roadmap_completion_feeds_progress_and_pending_skills(client):
    t = setup_user(client)
    client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": [], "career_goal": "AI/ML Engineer"}, headers=H(t))
    rm = client.get("/api/roadmap", headers=H(t)).json()
    before = client.get("/api/progress", headers=H(t)).json()
    assert before["roadmap"]["exists"] and before["roadmap"]["progress_percent"] == 0
    client.put(f"/api/roadmap/{rm['items'][0]['id']}", json={"completed": True}, headers=H(t))
    after = client.get("/api/progress", headers=H(t)).json()
    assert after["roadmap"]["completed"] == 1 and after["readiness_score"] > before["readiness_score"]
    assert set(rm["items"][0]["skills"]) <= set(after["pending_skills"])
    only = client.post("/api/progress/apply-skills", json={"skills": [rm["items"][0]["skills"][0]]}, headers=H(t)).json()
    assert len(only["pending_skills"]) == len(after["pending_skills"]) - 1


def test_progress_is_isolated_per_user(client):
    a, b = setup_user(client), setup_user(client)
    for t in (a, b):
        client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": ["Python"], "career_goal": "Data Scientist"}, headers=H(t))
    client.put("/api/progress/courses/kaggle-pandas", json={"status": "completed"}, headers=H(a))
    assert client.get("/api/progress/courses", headers=H(b)).json() == {}
