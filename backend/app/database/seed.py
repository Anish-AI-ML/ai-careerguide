import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models.models import Skill

SKILLS_PATH = Path(__file__).resolve().parents[3] / "data" / "skills.json"

def seed_skills(db: Session) -> int:
    """Insert catalog skills that are missing (idempotent). Returns how many were added."""
    existing = set(db.scalars(select(Skill.name_key)))
    added = 0
    for s in json.loads(SKILLS_PATH.read_text(encoding="utf-8")):
        if s["key"] not in existing:
            db.add(Skill(name_key=s["key"], name=s["name"], category=s["stage"]))
            added += 1
    db.commit()
    return added
