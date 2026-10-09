"""Transparent course recommender: ranks courses by the skill gaps they close."""
import json
from pathlib import Path
from app.services.career_recommendation import norm

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "courses.json"
_SPECIAL = {"sql": "SQL", "nlp": "NLP", "ci/cd": "CI/CD", "css": "CSS", "html": "HTML", "node.js": "Node.js", "mlops": "MLOps",
            "c++": "C++", "opencv": "OpenCV", "mongodb": "MongoDB", "pytorch": "PyTorch", "tensorflow": "TensorFlow"}


def pretty(skill: str) -> str:
    return _SPECIAL.get(skill, skill.title())


def load_courses(path: Path = DATA_PATH) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def recommend_courses(gaps: list[str], user_skills, career_name: str, *, exclude=(), limit: int = 6, courses: list[dict] | None = None, context: str | None = None) -> dict:
    """gaps must be ordered by importance (earlier = more important)."""
    courses = courses if courses is not None else load_courses()
    have = {norm(s) for s in user_skills}
    gaps = [norm(g) for g in gaps]
    weight = {g: 1 - 0.5 * i / max(1, len(gaps)) for i, g in enumerate(gaps)}
    cands = []
    for c in courses:
        if c["id"] in exclude:
            continue
        covers = [g for g in gaps if g in c["skills"]]
        if not covers:
            continue
        pre = c["prerequisites"]
        missing = [p for p in pre if p not in have]
        ready = 1.0 if not pre else 1 - len(missing) / len(pre)
        score = max(weight[g] for g in covers) * (1 + 0.1 * (len(covers) - 1)) * (0.6 + 0.4 * ready) + (0.05 if c["free"] else 0)
        cands.append((score, c, covers, missing))
    cands.sort(key=lambda x: (-x[0], x[1]["id"]))

    picked, covered = [], set()
    for item in cands:  # pass 1: best course per uncovered gap
        if len(picked) < limit and set(item[2]) - covered:
            picked.append(item); covered |= set(item[2])
    for item in cands:  # pass 2: fill remaining slots
        if len(picked) < limit and item not in picked:
            picked.append(item)

    recs = []
    for score, c, covers, missing in picked:
        main = pretty(covers[0])
        note = (f" Learn first: {', '.join(pretty(m) for m in missing)}." if missing
                else " You already meet the prerequisites." if c["prerequisites"] else " No prerequisites needed.")
        recs.append({**c, "score": round(score, 2), "covers": covers, "missing_prerequisites": missing,
                     "reason": f"{main} is missing from your profile and {context or f'is a core skill for {career_name}'}.{note}"})
    offered = {s for c in courses for s in c["skills"]}
    return {"courses": recs, "uncovered_skills": [g for g in gaps if g not in offered]}
