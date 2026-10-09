import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated
from app.api.deps import ai_rate_limit, current_user
from app.api.profile import profile_dict
from app.api.recommendations import pick_target
from app.database.session import get_db
from ..models.models import ChatMessage, ChatSession, ResumeAnalysis, Roadmap, User
from app.services import career_recommendation as engine
from app.services.career_chatbot import SUGGESTIONS, reply_for
from app.services.roadmap_generator import generate_roadmap

router = APIRouter(prefix="/api/chat", tags=["chat"])
MAX_MESSAGES = 200


class ChatRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    session_id: uuid.UUID | None = None


def build_context(db: Session, user: User) -> dict:
    profile = profile_dict(db, user)
    ranked = engine.analyze(profile or {})
    target = pick_target(ranked, None) if profile else ranked[0]
    rm = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id))
    if rm and rm.career_id == target["id"]:
        phases = [{"phase": i.phase, "title": i.title, "skills": i.skills, "est_weeks": i.est_weeks, "courses": i.courses,
                   "projects": i.projects, "completed": i.completed} for i in rm.items]
    elif profile:
        phases = [{**p, "completed": False} for p in generate_roadmap(target["skill_gaps"], profile["skills"], target["career"])]
    else:
        phases = None
    last = db.scalar(select(ResumeAnalysis).where(ResumeAnalysis.user_id == user.id).order_by(ResumeAnalysis.created_at.desc()))
    return {"name": user.full_name.split()[0], "has_profile": bool(profile), "profile": profile or {}, "ranked": ranked,
            "target": target, "roadmap": phases, "resume": last.result if last else None}


def _owned(db: Session, user: User, sid: uuid.UUID) -> ChatSession:
    s = db.get(ChatSession, sid)
    if not s or s.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return s


@router.get("/suggestions")
def suggestions():
    return SUGGESTIONS


@router.post("", dependencies=[Depends(ai_rate_limit)])
def chat(req: ChatRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = _owned(db, user, req.session_id) if req.session_id else ChatSession(user_id=user.id, title=req.message[:60])
    history = [{"role": m.role, "content": m.content} for m in session.messages] if req.session_id else []
    if len(history) >= MAX_MESSAGES:
        raise HTTPException(status_code=409, detail="This conversation is too long. Please start a new chat.")
    text, mode = reply_for(req.message, build_context(db, user), history)
    t0 = datetime.now(timezone.utc)
    session.messages.append(ChatMessage(role="user", content=req.message, created_at=t0))
    session.messages.append(ChatMessage(role="assistant", content=text, created_at=t0 + timedelta(milliseconds=1)))
    db.add(session)
    db.commit()
    return {"session_id": str(session.id), "reply": text, "mode": mode}


@router.get("/history")
def history(session_id: uuid.UUID | None = Query(None), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if session_id:
        s = _owned(db, user, session_id)
        return [{"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in s.messages]
    rows = db.scalars(select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.created_at.desc()).limit(30))
    return [{"id": str(s.id), "title": s.title or "New chat", "created_at": s.created_at.isoformat()} for s in rows]


@router.delete("/{session_id}", status_code=204)
def clear(session_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_owned(db, user, session_id))
    db.commit()
    return Response(status_code=204)
