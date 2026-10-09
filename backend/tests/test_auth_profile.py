import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.models import User


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def reg(client, pw="correct-horse-1"):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"full_name": "Test User", "email": email, "password": pw})
    return email, r


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_login_me_and_hashing(client):
    email, r = reg(client)
    assert r.status_code == 201
    tok = r.json()["access_token"]
    assert client.get("/api/auth/me", headers=auth(tok)).json()["email"] == email
    with SessionLocal() as db:
        h = db.query(User).filter_by(email=email).one().password_hash
    assert h.startswith("$2") and "correct-horse-1" not in h
    assert client.post("/api/auth/login", json={"email": email.upper(), "password": "correct-horse-1"}).status_code == 200


def test_login_failures_are_generic(client):
    email, _ = reg(client)
    bad = client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
    ghost = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert bad.status_code == ghost.status_code == 401
    assert bad.json() == ghost.json()


def test_register_validation_and_duplicate(client):
    email, _ = reg(client)
    dup = client.post("/api/auth/register", json={"full_name": "Dup", "email": email, "password": "another-pass-1"})
    assert dup.status_code == 409
    assert client.post("/api/auth/register", json={"full_name": "X Y", "email": "a@b.co", "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={"full_name": "X Y", "email": "not-an-email", "password": "long-enough-1"}).status_code == 422


def test_protected_routes_need_valid_token(client):
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/profile", headers=auth("garbage")).status_code == 401


def test_profile_roundtrip_and_dedupe(client):
    _, r = reg(client)
    h = auth(r.json()["access_token"])
    assert client.get("/api/profile", headers=h).status_code == 404
    body = {"degree": "B.E.", "branch": "CSE", "cgpa": 8.5, "skills": ["Python", "python", "Docker"],
            "interests": ["NLP"], "projects": ["Traffic model"], "career_goal": "AI/ML Engineer"}
    put = client.put("/api/profile", json=body, headers=h)
    assert put.status_code == 200 and put.json()["skills"] == ["Docker", "Python"]
    body["skills"] = ["Python"]
    assert client.put("/api/profile", json=body, headers=h).json()["skills"] == ["Python"]
    assert client.get("/api/profile", headers=h).json()["career_goal"] == "AI/ML Engineer"
    assert client.put("/api/profile", json={**body, "cgpa": 14}, headers=h).status_code == 422


def test_profiles_are_isolated_per_user(client):
    _, a = reg(client); _, b = reg(client)
    client.put("/api/profile", json={"degree": "A", "skills": ["Rust"]}, headers=auth(a.json()["access_token"]))
    assert client.get("/api/profile", headers=auth(b.json()["access_token"])).status_code == 404


def test_skills_endpoints(client):
    _, r = reg(client)
    custom = f"Custom Skill {uuid.uuid4().hex[:6]}"
    assert client.post("/api/skills", json={"name": custom}).status_code == 401
    h = auth(r.json()["access_token"])
    assert client.post("/api/skills", json={"name": custom}, headers=h).status_code == 201
    assert client.post("/api/skills", json={"name": custom.lower()}, headers=h).status_code == 200
    assert client.post("/api/skills", json={"name": "kubernetes"}, headers=h).status_code == 200  # already in the seeded catalog
    assert custom in [s["name"] for s in client.get("/api/skills").json()]


def test_catalog_skills_are_seeded_and_seeding_is_idempotent(client):
    from app.database.seed import seed_skills
    names = [s["name"] for s in client.get("/api/skills").json()]
    assert {"Python", "PyTorch", "MLOps", "Node.js"} <= set(names) and len(names) >= 40
    with SessionLocal() as db:
        assert seed_skills(db) == 0
