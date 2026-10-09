import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import career_chatbot as bot
from app.services import career_recommendation as engine
from app.services.roadmap_generator import generate_roadmap

H = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731
PROFILE = {"education": {"branch": "Computer Science (AI & ML)", "cgpa": 8.5}, "skills": ["Python", "TensorFlow", "Machine Learning", "SQL", "Git"],
           "interests": ["Artificial Intelligence"], "projects": ["Traffic prediction with TensorFlow"], "certifications": [], "experience": [],
           "career_goal": "AI/ML Engineer"}


def ctx(profile=PROFILE, resume=None):
    ranked = engine.analyze(profile or {})
    target = next((r for r in ranked if r["is_goal"]), ranked[0])
    phases = [{**p, "completed": False} for p in generate_roadmap(target["skill_gaps"], (profile or {}).get("skills", []), target["career"])] if profile else None
    return {"name": "Anish", "has_profile": bool(profile), "profile": profile or {}, "ranked": ranked, "target": target, "roadmap": phases, "resume": resume}


@pytest.mark.parametrize("q,expect", [
    ("Which career is best for me?", "closest career matches"), ("What should I learn next?", "Phase 1"),
    ("How can I become an AI engineer?", "AI/ML Engineer"), ("Which skills am I missing?", "still missing"),
    ("What projects should I build?", "Projects that would close gaps"), ("Am I ready for an internship?", "✓"),
    ("Review my resume.", "Resume page"), ("Recommend some courses", "Courses I would start with"), ("hello", "CareerAI"),
    ("zzz qqq", "I can help with")])
def test_local_intents(q, expect):
    assert expect in bot.local_reply(q, ctx())


def test_roadmap_months_and_career_detection():
    out = bot.local_reply("Give me a 6-month roadmap", ctx())
    assert "Weeks 1-" in out and "AI/ML Engineer" in out
    short = bot.local_reply("Give me a 1-month roadmap for data analyst", ctx())
    assert "Data Analyst" in short and "continue after month 1" in short


def test_resume_answer_uses_stored_analysis():
    res = {"resume_score": 71, "role_match": {"overall": 64}, "target": {"career": "AI/ML Engineer"}, "ats_suggestions": ["Add numbers"], "technical_skill_gaps": ["mlops"]}
    out = bot.local_reply("review my resume", ctx(resume=res))
    assert "71/100" in out and "Add numbers" in out and "MLOps" in out


def test_no_profile_asks_to_complete_it_but_generic_questions_work():
    assert "Complete the onboarding" in bot.local_reply("Which career is best for me?", ctx(profile=None))
    assert "Data Scientist" in bot.local_reply("How can I become a data scientist?", ctx(profile=None))


def test_llm_used_when_configured_and_falls_back_on_error(monkeypatch):
    for k, v in (("LLM_API_BASE", "http://x"), ("LLM_API_KEY", "k"), ("LLM_MODEL", "m")):
        monkeypatch.setenv(k, v)
    seen = {}
    monkeypatch.setattr(bot, "call_llm", lambda msgs: seen.setdefault("m", msgs) and "LLM says hi")
    assert bot.reply_for("hi there", ctx(), [{"role": "user", "content": "earlier"}]) == ("LLM says hi", "llm")
    assert seen["m"][0]["role"] == "system" and "Python" in seen["m"][0]["content"] and seen["m"][-1]["content"] == "hi there"
    def boom(_): raise RuntimeError("down")
    monkeypatch.setattr(bot, "call_llm", boom)
    text, mode = bot.reply_for("Which career is best for me?", ctx())
    assert mode == "local" and "closest career matches" in text


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def token(client):
    return client.post("/api/auth/register", json={"full_name": "Chat Tester", "email": f"{uuid.uuid4().hex[:8]}@example.com", "password": "chat-bot-pass-1"}).json()["access_token"]


def test_api_flow_history_ownership_and_clear(client):
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 401
    assert client.get("/api/chat/suggestions").status_code == 200
    t = token(client)
    client.put("/api/profile", json={"degree": "B.E.", "branch": "CSE", "skills": ["Python", "ML"], "career_goal": "AI/ML Engineer"}, headers=H(t))
    r = client.post("/api/chat", json={"message": "Which skills am I missing?"}, headers=H(t))
    assert r.status_code == 200 and r.json()["mode"] == "local" and "still missing" in r.json()["reply"]
    sid = r.json()["session_id"]
    r2 = client.post("/api/chat", json={"message": "What should I learn next?", "session_id": sid}, headers=H(t))
    assert r2.json()["session_id"] == sid
    msgs = client.get(f"/api/chat/history?session_id={sid}", headers=H(t)).json()
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
    assert client.get("/api/chat/history", headers=H(t)).json()[0]["id"] == sid
    other = token(client)
    assert client.get(f"/api/chat/history?session_id={sid}", headers=H(other)).status_code == 404
    assert client.post("/api/chat", json={"message": "x", "session_id": sid}, headers=H(other)).status_code == 404
    assert client.delete(f"/api/chat/{sid}", headers=H(other)).status_code == 404
    assert client.delete(f"/api/chat/{sid}", headers=H(t)).status_code == 204
    assert client.get("/api/chat/history", headers=H(t)).json() == []


def test_validation(client):
    t = token(client)
    assert client.post("/api/chat", json={"message": "   "}, headers=H(t)).status_code == 422
    assert client.post("/api/chat", json={"message": "a" * 1001}, headers=H(t)).status_code == 422
    r = client.post("/api/chat", json={"message": "Which career is best for me?"}, headers=H(t))  # no profile yet
    assert r.status_code == 200 and "Complete the onboarding" in r.json()["reply"]
