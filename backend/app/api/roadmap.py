import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.api.profile import profile_dict
from app.api.recommendations import pick_target
from app.database.session import get_db
from ..models.models import Roadmap, RoadmapItem, User
from app.services import career_recommendation as engine
from app.services.roadmap_generator import generate_roadmap

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


class GenerateRequest(BaseModel):
    career_id: str | None = Field(None, max_length=60)


class ItemUpdate(BaseModel):
    completed: bool


def _out(rm: Roadmap) -> dict:
    done = sum(1 for i in rm.items if i.completed)
    return {"id": str(rm.id), "career": rm.career_name, "career_id": rm.career_id,
            "progress_percent": round(100 * done / len(rm.items)) if rm.items else 0,
            "total_weeks": sum(i.est_weeks for i in rm.items),
            "items": [{"id": str(i.id), "phase": i.phase, "title": i.title, "skills": i.skills, "est_weeks": i.est_weeks,
                       "difficulty": i.difficulty, "courses": i.courses, "projects": i.projects, "completed": i.completed} for i in rm.items]}


def _build(db: Session, user: User, career_id: str | None) -> Roadmap:
    profile = profile_dict(db, user)
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first")
    target = pick_target(engine.analyze(profile), career_id)
    phases = generate_roadmap(target["skill_gaps"], profile["skills"], target["career"])

    old = db.query(Roadmap).filter_by(user_id=user.id).one_or_none()
    kept = {}
    if old:  # keep completion for phases that teach exactly the same skills
        kept = {frozenset(i.skills): i.completed_at or datetime.now(timezone.utc) for i in old.items if i.completed}
        db.delete(old)
        db.flush()
    rm = Roadmap(user_id=user.id, career_id=target["id"], career_name=target["career"])
    for ph in phases:
        done = kept.get(frozenset(ph["skills"]))
        rm.items.append(RoadmapItem(phase=ph["phase"], title=ph["title"], skills=ph["skills"], est_weeks=ph["est_weeks"],
                                    difficulty=ph["difficulty"], courses=ph["courses"], projects=ph["projects"],
                                    completed=done is not None, completed_at=done))
    db.add(rm)
    db.commit()
    return rm


@router.get("")
def get_roadmap(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rm = db.query(Roadmap).filter_by(user_id=user.id).one_or_none()
    return _out(rm or _build(db, user, None))  # first visit generates from the saved profile


@router.post("/generate")
def regenerate(body: GenerateRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _out(_build(db, user, body.career_id))


@router.put("/{item_id}")
def update_item(item_id: uuid.UUID, body: ItemUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(RoadmapItem, item_id)
    if not item or item.roadmap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    item.completed = body.completed
    item.completed_at = datetime.now(timezone.utc) if body.completed else None
    db.commit()
    return _out(item.roadmap)
