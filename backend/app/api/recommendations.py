from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import ai_rate_limit, current_user
from app.api.profile import profile_dict
from app.database.session import get_db
from ..models.models import Profile, User
from app.schemas.recommend import CourseRequest, CourseResponse
from app.services import career_recommendation as engine
from app.services.course_recommendation import recommend_courses

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def pick_target(ranked: list[dict], career_id: str | None) -> dict:
    if career_id:
        target = next((r for r in ranked if r["id"] == career_id), None)
        if not target:
            raise HTTPException(status_code=404, detail=f"Career '{career_id}' not found")
        return target
    return next((r for r in ranked if r["is_goal"]), ranked[0])


def _build(profile: dict, career_id: str | None, exclude, limit: int, weights=None) -> dict:
    try:
        ranked = engine.analyze(profile, weights)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    target = pick_target(ranked, career_id)
    out = recommend_courses(target["skill_gaps"], profile.get("skills", []), target["career"], exclude=set(exclude), limit=limit)
    return {"career": target["career"], "career_id": target["id"], "match_score": target["match_score"], **out}


@router.post("/courses", response_model=CourseResponse, dependencies=[Depends(ai_rate_limit)])
def courses_for_body(req: CourseRequest):
    profile = req.model_dump(exclude={"weights", "career_id", "exclude", "limit"})
    return _build(profile, req.career_id, req.exclude, req.limit, req.weights)


@router.get("/courses", response_model=CourseResponse, dependencies=[Depends(ai_rate_limit)])
def courses_for_me(career_id: str | None = Query(None, max_length=60), limit: int = Query(6, ge=1, le=20),
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_dict(db, user)
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first")
    return _build(profile, career_id, [], limit)
