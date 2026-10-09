import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.course_recommendation import load_courses, recommend_courses
from app.services.career_recommendation import load_careers

H = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731


def test_dataset_integrity():
    cs = load_courses()
    assert len(cs) >= 40 and len({c["id"] for c in cs}) == len(cs)
    for c in cs:
        assert c["url"].startswith("https://") and c["difficulty"] in {"beginner", "intermediate", "advanced"}
        assert c["skills"] and c["duration_hours"] > 0 and c["rating"] is None
    ids_skills = {s for c in cs for s in c["skills"]}
    assert all(p in ids_skills or p in {"python"} for c in cs for p in c["prerequisites"])


def test_core_skills_mostly_covered():
    offered = {s for c in load_courses() for s in c["skills"]}
    core = {s for car in load_careers() for s in car["core"]} - {"cloud"} | {"cloud"}
    uncovered = {s for s in core if s not in offered and s not in {"aws", "azure"}}
    assert uncovered <= {"data warehousing", "security tools"}


def test_recommend_reasons_and_prereqs():
    r = recommend_courses(["mlops", "pytorch", "docker"], ["python", "machine learning"], "AI/ML Engineer", limit=5)
    by = {c["id"]: c for c in r["courses"]}
    assert by["coursera-mlops"]["missing_prerequisites"] == []
    assert "MLOps is missing" in by["coursera-mlops"]["reason"]
    assert {"coursera-mlops", "pytorch-tutorials", "docker-start"} <= set(by)
    r2 = recommend_courses(["pytorch"], [], "AI/ML Engineer", limit=3)
    assert r2["courses"][0]["missing_prerequisites"]  # told what to learn first


def test_exclude_and_uncovered():
    r = recommend_courses(["docker", "data warehousing"], [], "Data Engineer", exclude={"docker-start"})
    assert all(c["id"] != "docker-start" for c in r["courses"])
    assert r["uncovered_skills"] == ["data warehousing"]


def test_deterministic_and_limit():
    a = recommend_courses(["python", "sql", "docker", "git"], [], "X", limit=2)
    assert a == recommend_courses(["python", "sql", "docker", "git"], [], "X", limit=2) and len(a["courses"]) == 2


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_api_post_and_get(client):
    body = {"skills": ["Python", "ML"], "interests": ["AI"], "career_goal": "AI/ML Engineer"}
    r = client.post("/api/recommendations/courses", json=body)
    assert r.status_code == 200 and r.json()["career"] == "AI/ML Engineer" and r.json()["courses"]
    assert client.post("/api/recommendations/courses", json={**body, "career_id": "nope"}).status_code == 404
    assert client.post("/api/recommendations/courses", json={**body, "career_id": "devops-engineer"}).json()["career"] == "DevOps Engineer"

    assert client.get("/api/recommendations/courses").status_code == 401
    tok = client.post("/api/auth/register", json={"full_name": "C U", "email": f"{uuid.uuid4().hex[:8]}@example.com", "password": "course-pass-1"}).json()["access_token"]
    assert client.get("/api/recommendations/courses", headers=H(tok)).status_code == 404
    client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": ["Python"], "career_goal": "AI/ML Engineer"}, headers=H(tok))
    g = client.get("/api/recommendations/courses?limit=3", headers=H(tok))
    assert g.status_code == 200 and len(g.json()["courses"]) == 3
