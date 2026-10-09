from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.api.profile import _skill, profile_dict
from app.api.recommendations import pick_target
from app.database.session import get_db
from ..models.models import ProgressSnapshot, Roadmap, User, UserCourse, UserSkill
from app.schemas.profile import Tag
from app.services import career_recommendation as engine
from app.services.course_recommendation import load_courses, pretty
from app.services.progress import readiness

router = APIRouter(prefix="/api/progress", tags=["progress"])
KEEP_SNAPSHOTS = 60


class StatusUpdate(BaseModel):
    status: Literal["none", "planned", "in_progress", "completed"]


class ApplySkills(BaseModel):
    skills: list[Tag] | None = Field(None, max_length=100)  # default: every pending skill


def _snapshot(db: Session, user: User, s: dict) -> None:
    key = (s["readiness_score"], s["skills"]["total_skills"], s["roadmap"]["progress_percent"], s["courses"]["completed"])
    last = db.scalar(select(ProgressSnapshot).where(ProgressSnapshot.user_id == user.id).order_by(ProgressSnapshot.created_at.desc()))
    if last and (last.readiness, last.skill_count, last.roadmap_percent, last.courses_completed) == key:
        return
    db.add(ProgressSnapshot(user_id=user.id, readiness=key[0], skill_count=key[1], roadmap_percent=key[2], courses_completed=key[3]))
    db.commit()
    old = db.scalars(select(ProgressSnapshot.id).where(ProgressSnapshot.user_id == user.id).order_by(ProgressSnapshot.created_at.desc()).offset(KEEP_SNAPSHOTS)).all()
    if old:
        db.execute(delete(ProgressSnapshot).where(ProgressSnapshot.id.in_(old)))
        db.commit()


def build_summary(db: Session, user: User) -> dict:
    profile = profile_dict(db, user)
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first")
    target = pick_target(engine.analyze(profile), None)
    have_core, gaps = target["strengths"], target["skill_gaps"]
    coverage = round(100 * len(have_core) / (len(have_core) + len(gaps))) if have_core or gaps else 100

    rm = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id))
    if rm and rm.items:
        done = sum(1 for i in rm.items if i.completed)
        roadmap = {"exists": True, "completed": done, "total": len(rm.items), "progress_percent": round(100 * done / len(rm.items))}
    else:
        roadmap = {"exists": False, "completed": 0, "total": 0, "progress_percent": 0 if gaps else 100}

    catalog = {c["id"]: c for c in load_courses()}
    rows = db.scalars(select(UserCourse).where(UserCourse.user_id == user.id)).all()
    items = [{"course_id": r.course_id, "title": catalog[r.course_id]["title"], "platform": catalog[r.course_id]["platform"],
              "url": catalog[r.course_id]["url"], "status": r.status, "completed_at": r.completed_at.isoformat() if r.completed_at else None}
             for r in rows if r.course_id in catalog]
    n = lambda st: sum(1 for i in items if i["status"] == st)  # noqa: E731
    courses = {"tracked": len(items), "completed": n("completed"), "in_progress": n("in_progress"), "planned": n("planned"),
               "completion_percent": round(100 * n("completed") / len(items)) if items else 0, "items": items}

    known = {engine.norm(s) for s in profile["skills"]}
    pending: list[str] = []
    sources = [s for i in items if i["status"] == "completed" for s in catalog[i["course_id"]]["skills"]]
    if rm:
        sources += [s for i in rm.items if i.completed for s in i.skills]
    for s in sources:
        if s not in known and s not in pending:
            pending.append(s)

    portfolio_n = len(profile["projects"]) + len(profile["certifications"])
    score, breakdown = readiness(coverage, roadmap["progress_percent"], portfolio_n, courses["completed"], courses["tracked"])
    summary = {"career": target["career"], "career_id": target["id"], "readiness_score": score, "readiness_breakdown": breakdown,
               "skills": {"coverage_percent": coverage, "core_have": have_core, "core_missing": gaps, "total_skills": len(profile["skills"])},
               "roadmap": roadmap, "courses": courses, "pending_skills": pending,
               "portfolio": {"projects": profile["projects"], "certifications": profile["certifications"]},
               "disclaimer": "The readiness score is a transparent estimate from your own data, not a prediction of hiring outcomes."}
    _snapshot(db, user, summary)
    snaps = db.scalars(select(ProgressSnapshot).where(ProgressSnapshot.user_id == user.id).order_by(ProgressSnapshot.created_at.desc()).limit(30)).all()
    summary["history"] = [{"at": x.created_at.isoformat(), "readiness": x.readiness, "skill_count": x.skill_count, "roadmap_percent": x.roadmap_percent,
                           "courses_completed": x.courses_completed} for x in reversed(snaps)]
    return summary


@router.get("")
def get_progress(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return build_summary(db, user)


@router.get("/courses")
def course_statuses(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {r.course_id: r.status for r in db.scalars(select(UserCourse).where(UserCourse.user_id == user.id))}


@router.put("/courses/{course_id}")
def set_course(course_id: str, body: StatusUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if len(course_id) > 60 or course_id not in {c["id"] for c in load_courses()}:
        raise HTTPException(status_code=404, detail="Course not found")
    row = db.get(UserCourse, (user.id, course_id))
    if body.status == "none":
        if row:
            db.delete(row)
    else:
        row = row or UserCourse(user_id=user.id, course_id=course_id, status=body.status)
        row.status = body.status
        row.completed_at = datetime.now(timezone.utc) if body.status == "completed" else None
        db.add(row)
    db.commit()
    return build_summary(db, user)


@router.post("/apply-skills")
def apply_skills(body: ApplySkills, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pending = build_summary(db, user)["pending_skills"]
    chosen = pending if body.skills is None else [s for s in pending if s in {engine.norm(x) for x in body.skills}]
    for s in chosen:
        sk, _ = _skill(db, pretty(s))
        if not db.get(UserSkill, (user.id, sk.id)):
            db.add(UserSkill(user_id=user.id, skill_id=sk.id))
    db.commit()
    return build_summary(db, user)
