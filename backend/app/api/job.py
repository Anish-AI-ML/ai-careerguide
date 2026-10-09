import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import ai_rate_limit, current_user
from app.api.profile import profile_dict
from app.database.session import get_db
from ..models.models import JobAnalysis, User
from app.schemas.profile import Tag
from app.services.job_analyzer import analyze_job

router = APIRouter(prefix="/api/job", tags=["job"])


class JobRequest(BaseModel):
    description: str = Field(min_length=50, max_length=20000)
    title: str = Field("", max_length=120)
    skills: list[Tag] | None = Field(None, max_length=100)  # optional override; defaults to the saved profile


@router.post("/analyze", dependencies=[Depends(ai_rate_limit)])
def analyze(req: JobRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    skills = req.skills
    if skills is None:
        profile = profile_dict(db, user)
        if not profile:
            raise HTTPException(status_code=422, detail="Complete your profile first so we can compare your skills")
        skills = profile["skills"]
    try:
        result = analyze_job(req.description, skills)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    row = JobAnalysis(user_id=user.id, title=req.title.strip(), match_score=result["match_score"], result=result)
    db.add(row)
    db.commit()
    return {"id": str(row.id), "title": row.title, **result}


@router.get("/history")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(JobAnalysis).where(JobAnalysis.user_id == user.id).order_by(JobAnalysis.created_at.desc()).limit(10))
    return [{"id": str(r.id), "title": r.title or "Untitled job", "match_score": r.match_score, "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/{job_id}")
def get_one(job_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(JobAnalysis, job_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"id": str(row.id), "title": row.title, **row.result}
