from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.database.session import get_db
from ..models.models import Profile, Skill, User, UserSkill
from app.schemas.profile import ProfileData, SkillIn, SkillOut

router = APIRouter(prefix="/api", tags=["profile"])


def _skill(db: Session, name: str) -> tuple[Skill, bool]:
    key = name.strip().lower()
    s = db.scalar(select(Skill).where(Skill.name_key == key))
    if s:
        return s, False
    s = Skill(name_key=key, name=name.strip())
    db.add(s)
    db.flush()
    return s, True


def _skill_names(db: Session, user_id) -> list[str]:
    q = select(Skill.name).join(UserSkill, UserSkill.skill_id == Skill.id).where(UserSkill.user_id == user_id).order_by(Skill.name)
    return list(db.scalars(q))


def profile_dict(db: Session, user: User) -> dict | None:
    """Profile in the shape the recommendation engine expects (None if not set up)."""
    p = db.get(Profile, user.id)
    if not p:
        return None
    return {"education": {"degree": p.degree, "branch": p.branch, "institution": p.institution, "year": p.current_year, "cgpa": p.cgpa},
            "skills": _skill_names(db, user.id), "interests": p.interests, "projects": p.projects,
            "certifications": p.certifications, "experience": p.experience, "career_goal": p.career_goal}


@router.get("/profile", response_model=ProfileData)
def get_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(Profile, user.id)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not set up yet")
    return ProfileData(degree=p.degree, branch=p.branch, institution=p.institution, current_year=p.current_year, cgpa=p.cgpa,
                       skills=_skill_names(db, user.id), interests=p.interests, projects=p.projects,
                       certifications=p.certifications, experience=p.experience, career_goal=p.career_goal)


@router.put("/profile", response_model=ProfileData)
def put_profile(data: ProfileData, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(Profile, user.id) or Profile(user_id=user.id)
    for f in ("degree", "branch", "institution", "current_year", "cgpa", "interests", "projects", "certifications", "experience", "career_goal"):
        setattr(p, f, getattr(data, f))
    db.add(p)
    db.execute(delete(UserSkill).where(UserSkill.user_id == user.id))
    seen: set[str] = set()
    for name in data.skills:
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        db.add(UserSkill(user_id=user.id, skill_id=_skill(db, name)[0].id))
    db.commit()
    return get_profile(user, db)


@router.get("/skills", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    return [{"id": s.id, "name": s.name} for s in db.scalars(select(Skill).order_by(Skill.name))]


@router.post("/skills", response_model=SkillOut, status_code=201)
def add_skill(body: SkillIn, response: Response, _: User = Depends(current_user), db: Session = Depends(get_db)):
    s, created = _skill(db, body.name)
    db.commit()
    if not created:
        response.status_code = 200
    return {"id": s.id, "name": s.name}
