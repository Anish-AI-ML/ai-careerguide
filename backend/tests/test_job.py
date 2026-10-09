import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.job_analyzer import analyze_job

JD = """Machine Learning Engineer
We are hiring an engineer to ship models.
Responsibilities:
- Build and deploy models using Python and TensorFlow
Requirements:
- 3+ years of experience in machine learning
- Strong Python and SQL skills
- Experience with Docker and AWS
- Bachelor's degree in Computer Science or related field
Nice to have:
- Kubernetes
- Experience with PyTorch is a plus
"""
H = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731


def test_required_vs_preferred_and_requirements():
    r = analyze_job(JD, ["Python", "SQL", "ML", "TensorFlow"])
    assert set(r["required_skills"]) == {"python", "tensorflow", "machine learning", "sql", "docker", "cloud"}
    assert set(r["preferred_skills"]) == {"kubernetes", "pytorch"}
    assert r["experience_requirements"][0]["min_years"] == 3
    assert r["education_requirements"]["levels"] == ["bachelor"]
    assert set(r["should_improve"]) == {"docker", "cloud"} and set(r["preferred_missing"]) == {"kubernetes", "pytorch"}


def test_score_math_and_course_reasons():
    r = analyze_job(JD, ["Python", "SQL", "ML", "TensorFlow"])
    assert r["breakdown"] == {"required_match": 67, "preferred_match": 0}
    assert r["match_score"] == round(100 * 0.8 * 4 / 6)
    assert any("requested in this job description" in c["reason"] for c in r["recommended_courses"])
    full = analyze_job(JD, ["python", "tensorflow", "ml", "sql", "docker", "aws", "kubernetes", "pytorch"])
    assert full["match_score"] == 100 and full["recommended_courses"] == []


def test_required_wins_and_lines_cues():
    r = analyze_job("Requirements:\n- Python\nNice to have:\n- Python and Go\n- Docker would be a bonus\n- Must know SQL", [])
    assert "python" in r["required_skills"] and "python" not in r["preferred_skills"]
    assert "docker" in r["preferred_skills"] and "sql" in r["required_skills"]


def test_no_skills_raises_and_be_word_not_degree():
    with pytest.raises(ValueError):
        analyze_job("We value kindness, curiosity and a great attitude to learning every day.", [])
    r = analyze_job("Requirements:\n- Python experience\n- You will be part of a friendly team", [])
    assert r["education_requirements"]["levels"] == []


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def token(client):
    r = client.post("/api/auth/register", json={"full_name": "J M", "email": f"{uuid.uuid4().hex[:8]}@example.com", "password": "job-match-pass-1"})
    return r.json()["access_token"]


def test_api_flow(client):
    assert client.post("/api/job/analyze", json={"description": JD}).status_code == 401
    t = token(client)
    assert client.post("/api/job/analyze", json={"description": "too short"}, headers=H(t)).status_code == 422
    assert client.post("/api/job/analyze", json={"description": JD}, headers=H(t)).status_code == 422  # no profile
    assert client.post("/api/job/analyze", json={"description": "x " * 40}, headers=H(t)).status_code == 422
    client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": ["Python", "SQL"]}, headers=H(t))
    r = client.post("/api/job/analyze", json={"description": JD, "title": "ML Engineer"}, headers=H(t))
    assert r.status_code == 200 and r.json()["title"] == "ML Engineer" and "python" in r.json()["you_have"]
    hist = client.get("/api/job/history", headers=H(t)).json()
    assert hist[0]["id"] == r.json()["id"] and hist[0]["match_score"] == r.json()["match_score"]
    assert client.get(f"/api/job/{r.json()['id']}", headers=H(t)).json()["match_score"] == r.json()["match_score"]
    other = token(client)
    assert client.get(f"/api/job/{r.json()['id']}", headers=H(other)).status_code == 404
    over = client.post("/api/job/analyze", json={"description": JD, "skills": ["Docker"]}, headers=H(other))
    assert over.status_code == 200 and "docker" in over.json()["you_have"]
