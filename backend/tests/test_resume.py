import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.resume_analyzer import analyze_resume, split_sections, guess_name
from app.services.skill_extraction import extract_skills
from app.services.career_recommendation import load_careers
from tests.pdfutil import GOOD, WEAK, make_pdf

AI = next(c for c in load_careers() if c["id"] == "ai-ml-engineer")
H = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731


def test_extract_skills_boundaries_and_aliases():
    s = extract_skills("Worked with JavaScript, C++ and Java; AWS, scikit-learn, Node.js. Learned about C only.")
    assert {"javascript", "c++", "java", "cloud", "machine learning", "node.js"} <= set(s)
    assert "c" not in s and "r" not in s
    assert extract_skills("javascript only") == ["javascript"]  # must not also report java


def test_sections_and_name():
    sec = split_sections("\n".join(GOOD))
    assert {"education", "skills", "projects", "experience", "certifications", "achievements"} <= set(sec)
    assert guess_name(sec["header"]) == "Jane Doe"


def test_good_resume_scores_higher_than_weak_and_is_explainable():
    good, weak = analyze_resume("\n".join(GOOD), AI), analyze_resume("\n".join(WEAK), AI)
    assert good["resume_score"] > weak["resume_score"] + 25
    assert good["role_match"]["skills"] > weak["role_match"]["skills"]
    assert sum(v["points"] for v in good["score_breakdown"].values()) == pytest.approx(good["resume_score"], abs=1)
    assert "mlops" in good["technical_skill_gaps"] and good["recommended_courses"]
    assert good["extracted"]["technologies"] and any("Traffic" in p for p in good["extracted"]["projects"])
    assert any("Projects" in s for s in weak["ats_suggestions"]) and weak["project_suggestions"]
    assert 0 <= good["resume_score"] <= 100 and all(0 <= v <= 100 for v in good["role_match"].values())


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def token(client):
    r = client.post("/api/auth/register", json={"full_name": "R S", "email": f"{uuid.uuid4().hex[:8]}@example.com", "password": "resume-pass-1"})
    return r.json()["access_token"]


def up(client, t, data, name="cv.pdf", ctype="application/pdf", **form):
    return client.post("/api/resume/analyze", headers=H(t), files={"file": (name, data, ctype)}, data=form)


def test_upload_validation(client):
    t = token(client)
    assert client.post("/api/resume/analyze", files={"file": ("cv.pdf", b"x", "application/pdf")}).status_code == 401
    assert up(client, t, b"hello", "cv.txt", "text/plain").status_code == 415
    assert up(client, t, b"not really a pdf", "cv.pdf").status_code == 415
    assert up(client, t, make_pdf([["short"]]), career_id="ai-ml-engineer").status_code == 422  # no readable text
    assert up(client, t, make_pdf([GOOD] * 11), career_id="ai-ml-engineer").status_code == 422  # too many pages
    assert up(client, t, make_pdf([GOOD]), career_id="nope").status_code == 404
    assert up(client, t, make_pdf([GOOD])).status_code == 422  # no career and no profile


def test_size_limit(client, monkeypatch):
    monkeypatch.setenv("RESUME_MAX_MB", "0.001")
    t = token(client)
    assert up(client, t, b"%PDF-" + b"0" * 5000).status_code == 413


def test_happy_path_and_latest(client):
    t = token(client)
    assert client.get("/api/resume/latest", headers=H(t)).status_code == 404
    r = up(client, t, make_pdf([GOOD]), career_id="ai-ml-engineer")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["name"] == "Jane Doe" and d["target"]["career"] == "AI/ML Engineer" and d["resume_score"] > 50
    assert client.get("/api/resume/latest", headers=H(t)).json()["id"] == d["id"]
    client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": ["Python"], "career_goal": "Data Scientist"}, headers=H(t))
    assert up(client, t, make_pdf([GOOD])).json()["target"]["career"] == "Data Scientist"  # defaults to profile goal
