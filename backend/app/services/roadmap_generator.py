"""Builds a phased learning roadmap from skill gaps. Deterministic, no external calls."""
import json, math
from pathlib import Path
from app.services.career_recommendation import norm
from app.services.course_recommendation import load_courses, pretty, recommend_courses

IDEAS_PATH = Path(__file__).resolve().parents[3] / "data" / "project_ideas.json"
# Learning order: lower rank = learn earlier. Unknown skills default to 3.
RANK = {**{s: 1 for s in ("python", "statistics", "git", "linux", "sql", "html", "css", "javascript", "java", "c++", "excel", "networking")},
        **{s: 2 for s in ("pandas", "data visualization", "data structures", "cryptography", "mongodb", "power bi", "docker", "cloud", "typescript")},
        **{s: 3 for s in ("machine learning", "react", "node.js", "kubernetes", "terraform", "ci/cd", "spark", "system design", "penetration testing", "opencv", "airflow")},
        **{s: 4 for s in ("deep learning", "tensorflow", "pytorch", "nlp", "computer vision", "transformers")},
        **{s: 5 for s in ("mlops", "monitoring", "security tools", "data warehousing", "kafka")}}
LEVELS = ["beginner", "intermediate", "advanced"]
MAX_SKILLS_PER_PHASE = 3


def load_ideas(path: Path = IDEAS_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_roadmap(gaps: list[str], user_skills, career_name: str, *, hours_per_week: int = 8,
                     courses: list[dict] | None = None, ideas: dict | None = None) -> list[dict]:
    courses = courses if courses is not None else load_courses()
    ideas = ideas if ideas is not None else load_ideas()
    have = {norm(s) for s in user_skills}
    gaps = list(dict.fromkeys(norm(g) for g in gaps if norm(g) not in have))
    groups: dict[int, list[str]] = {}
    for g in gaps:
        groups.setdefault(RANK.get(g, 3), []).append(g)

    phases = []
    for rank in sorted(groups):
        skills = groups[rank]
        for i in range(0, len(skills), MAX_SKILLS_PER_PHASE):
            chunk = skills[i:i + MAX_SKILLS_PER_PHASE]
            rec = recommend_courses(chunk, have, career_name, limit=min(3, len(chunk) + 1), courses=courses)["courses"]
            hours = sum(c["duration_hours"] for c in rec)
            levels = [LEVELS.index(c["difficulty"]) for c in rec]
            diff = LEVELS[max(levels)] if levels else ("beginner" if rank <= 2 else "intermediate" if rank <= 4 else "advanced")
            projects = [ideas[s][0] if s in ideas else f"Build a small project that applies {pretty(s)}" for s in chunk[:2]]
            phases.append({"phase": len(phases) + 1,
                           "title": " + ".join(pretty(s) for s in chunk[:3]),
                           "skills": chunk,
                           "est_weeks": max(1, math.ceil(hours / hours_per_week)) if rec else 2,
                           "difficulty": diff,
                           "courses": [{k: c[k] for k in ("id", "title", "url", "platform", "duration_hours")} for c in rec],
                           "projects": projects})
            have |= set(chunk)  # later phases may assume earlier ones are learned
    return phases
