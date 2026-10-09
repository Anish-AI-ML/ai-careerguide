"""Transparent, configurable career scoring engine (no randomness, no external API)."""
import json, re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "careers.json"

GOAL_BONUS = 5  # transparent points added to the career the user explicitly chose

DEFAULT_WEIGHTS = {"skills": 0.40, "interests": 0.20, "education": 0.15,
                   "projects": 0.15, "experience": 0.10}

ALIASES = {"ml": "machine learning", "dl": "deep learning", "tf": "tensorflow",
           "js": "javascript", "ts": "typescript", "k8s": "kubernetes", "cv": "computer vision",
           "aws": "cloud", "azure": "cloud", "gcp": "cloud", "cloud computing": "cloud",
           "natural language processing": "nlp", "reactjs": "react", "nodejs": "node.js",
           "scikit-learn": "machine learning", "keras": "deep learning", "cicd": "ci/cd"}


def norm(s: str) -> str:
    s = s.strip().lower()
    return ALIASES.get(s, s)


def load_careers(path: Path = DATA_PATH) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_weights(weights: dict | None) -> dict:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    if any(v < 0 for v in w.values()) or sum(w.values()) <= 0:
        raise ValueError("weights must be non-negative with a positive sum")
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def _text(items) -> str:
    parts = []
    for it in items or []:
        parts.append(" ".join(map(str, it.values())) if isinstance(it, dict) else str(it))
    return " ".join(parts).lower()


def _mentions(text: str, term: str) -> bool:
    return re.search(r"(?<![\w])" + re.escape(term) + r"(?![\w])", text) is not None


def _skill_match(user_skills: set, career: dict):
    # core skills count double, nice-to-have count once
    got = [s for s in career["core"] if s in user_skills]
    got_nice = [s for s in career["nice"] if s in user_skills]
    total = 2 * len(career["core"]) + len(career["nice"])
    score = (2 * len(got) + len(got_nice)) / total if total else 0
    return score, got, [s for s in career["core"] if s not in user_skills]


def _interest_match(interests: set, career: dict) -> float:
    hits = len(interests & {norm(i) for i in career["interests"]})
    return min(1.0, hits / min(2, len(career["interests"])))


def _education_match(edu: dict, career: dict) -> float:
    field = f"{edu.get('degree','')} {edu.get('branch','')}".lower()
    base = 1.0 if any(k in field for k in career["education"]) else (0.6 if any(k in field for k in ("engineering", "technology", "science")) else 0.3)
    try:
        cgpa = max(0.0, min(float(edu.get("cgpa", 0)) / 10.0, 1.0))  # assumes 10-point scale
    except (TypeError, ValueError):
        cgpa = 0.0
    return base * (0.85 + 0.15 * cgpa)


def _evidence(text: str, career: dict, needed: int) -> float:
    terms = career["core"] + career["nice"]
    hits = sum(1 for t in terms if _mentions(text, t))
    return min(1.0, hits / needed)


def analyze(profile: dict, weights: dict | None = None, careers: list[dict] | None = None) -> list[dict]:
    """Return careers ranked by compatibility, each with score breakdown and explanation."""
    w = normalize_weights(weights)
    careers = careers or load_careers()
    skills = {norm(s) for s in profile.get("skills", [])}
    interests = {norm(i) for i in profile.get("interests", [])}
    edu = profile.get("education", {}) or {}
    proj_text = _text(profile.get("projects"))
    exp_text = _text(profile.get("experience")) + " " + _text(profile.get("certifications"))
    goal = (profile.get("career_goal") or "").strip().lower()

    results = []
    for c in careers:
        c = {**c, "core": [norm(x) for x in c["core"]], "nice": [norm(x) for x in c["nice"]]}
        s, strengths, gaps = _skill_match(skills, c)
        parts = {"skills": s, "interests": _interest_match(interests, c),
                 "education": _education_match(edu, c),
                 "projects": _evidence(proj_text, c, 3),
                 "experience": _evidence(exp_text, c, 2)}
        is_goal = goal == c["name"].lower()
        bonus = GOAL_BONUS if is_goal else 0
        score = min(100, round(100 * sum(parts[k] * w[k] for k in w)) + bonus)
        reason = (f"Matches {len(strengths)} of {len(c['core'])} core skills"
                  + (f" ({', '.join(strengths[:4])})" if strengths else "") + ".")
        results.append({"id": c["id"], "career": c["name"], "match_score": score, "reason": reason,
                        "strengths": strengths, "skill_gaps": gaps,
                        "breakdown": {k: round(100 * v) for k, v in parts.items()},
                        "is_goal": is_goal, "goal_bonus": bonus,
                        "disclaimer": "Guidance estimate, not a guaranteed outcome."})
    return sorted(results, key=lambda r: (-r["match_score"], r["career"]))


# Public aliases for reuse by resume / job analyzers
skill_match = _skill_match
evidence = _evidence


def normalized_career(c: dict) -> dict:
    return {**c, "core": [norm(x) for x in c["core"]], "nice": [norm(x) for x in c["nice"]]}
