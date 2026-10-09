import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.roadmap_generator import generate_roadmap

H = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731
GAPS = ["python", "machine learning", "deep learning", "pytorch", "docker", "mlops", "cloud"]


def test_phases_follow_learning_order_and_cover_all_gaps():
    ph = generate_roadmap(GAPS, [], "AI/ML Engineer")
    order = [s for p in ph for s in p["skills"]]
    assert sorted(order) == sorted(GAPS)
    assert order.index("python") < order.index("machine learning") < order.index("deep learning") < order.index("mlops")
    assert [p["phase"] for p in ph] == list(range(1, len(ph) + 1))
    assert all(len(p["skills"]) <= 3 and p["est_weeks"] >= 1 and p["projects"] for p in ph)


def test_known_skills_are_skipped_and_empty_gaps_give_no_phases():
    ph = generate_roadmap(GAPS, ["Python", "ML"], "AI/ML Engineer")
    assert "python" not in [s for p in ph for s in p["skills"]]
    assert generate_roadmap([], [], "X") == []


def test_prerequisites_assumed_from_earlier_phases():
    from app.services.course_recommendation import load_courses
    by = {c["id"]: c for c in load_courses()}
    ph = generate_roadmap(["python", "machine learning"], [], "X")
    ml_phase = next(p for p in ph if "machine learning" in p["skills"])
    assert ml_phase["phase"] > 1  # python is learned first
    first = by[ml_phase["courses"][0]["id"]]
    assert set(first["prerequisites"]) <= {"python"}  # prerequisites satisfied by the earlier phase


def test_unknown_skill_gets_generic_project_and_default_weeks():
    ph = generate_roadmap(["quantum basketweaving"], [], "X", courses=[], ideas={})
    assert ph[0]["est_weeks"] == 2 and "Quantum Basketweaving" in ph[0]["projects"][0]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def user(client):
    r = client.post("/api/auth/register", json={"full_name": "R M", "email": f"{uuid.uuid4().hex[:8]}@example.com", "password": "road-map-pass-1"})
    return r.json()["access_token"]


def test_roadmap_api_flow(client):
    assert client.get("/api/roadmap").status_code == 401
    t = user(client)
    assert client.get("/api/roadmap", headers=H(t)).status_code == 404  # no profile yet
    client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": ["Python"], "career_goal": "AI/ML Engineer"}, headers=H(t))
    rm = client.get("/api/roadmap", headers=H(t)).json()
    assert rm["career"] == "AI/ML Engineer" and rm["progress_percent"] == 0 and rm["items"]
    first = rm["items"][0]["id"]
    done = client.put(f"/api/roadmap/{first}", json={"completed": True}, headers=H(t)).json()
    assert done["items"][0]["completed"] and done["progress_percent"] == round(100 / len(done["items"]))
    again = client.post("/api/roadmap/generate", json={}, headers=H(t)).json()
    assert again["items"][0]["completed"]  # completion survives regeneration
    assert client.put(f"/api/roadmap/{first}", json={"completed": False}, headers=H(t)).status_code == 404  # old id replaced
    other = client.post("/api/roadmap/generate", json={"career_id": "devops-engineer"}, headers=H(t)).json()
    assert other["career"] == "DevOps Engineer"


def test_cannot_update_someone_elses_item(client):
    a, b = user(client), user(client)
    for t in (a, b):
        client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": [], "career_goal": "AI/ML Engineer"}, headers=H(t))
    item = client.get("/api/roadmap", headers=H(a)).json()["items"][0]["id"]
    assert client.put(f"/api/roadmap/{item}", json={"completed": True}, headers=H(b)).status_code == 404
    assert client.put("/api/roadmap/not-a-uuid", json={"completed": True}, headers=H(a)).status_code == 422
