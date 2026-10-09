"""Extracts requirements from a pasted job description and compares them with a skill set."""
import re
from app.services.career_recommendation import norm
from app.services.course_recommendation import pretty, recommend_courses
from app.services.skill_extraction import extract_skills

PREF_HEAD = re.compile(r"^(?:preferred(?: qualifications| skills)?|nice[- ]to[- ]have(?:s)?|bonus(?: points)?|good to have|desirable|additional skills|plus(?:es)?)$", re.I)
REQ_HEAD = re.compile(r"^(?:requirements?|qualifications?|minimum qualifications|required(?: skills| qualifications)?|must[- ]haves?|what you(?:'|’)?ll need|what we(?:'|’)?re looking for|responsibilities|key skills|skills|about you)$", re.I)
PREF_LINE = re.compile(r"nice[- ]to[- ]have|a plus|preferred|bonus|good to have|desirable|advantage|is a plus|are a plus", re.I)
REQ_LINE = re.compile(r"\b(?:required|must have|must|mandatory|essential)\b", re.I)
YEARS = re.compile(r"\b(\d{1,2})\s*(?:\+|-|–|to)?\s*(\d{1,2})?\s*\+?\s*(?:years|yrs)\b", re.I)
# Word forms are case-insensitive; abbreviations are case-sensitive so the word "be" is not read as a B.E. degree.
LEVELS = {"bachelor": re.compile(r"(?i:bachelor|undergraduate)|\bB\.?\s?Tech\b|\bB\.E\b\.?|\bBE\b|\bB\.?Sc\b"),
          "master": re.compile(r"(?i:master|postgraduate)|\bM\.?\s?Tech\b|\bM\.?Sc\b|\bMBA\b"),
          "phd": re.compile(r"ph\.?d|doctorate", re.I)}


def _heading(line: str) -> str | None:
    bare = line.strip().rstrip(":").strip("*#- ").strip()
    if not bare or len(bare) > 60 or not (line.rstrip().endswith(":") or PREF_HEAD.match(bare) or REQ_HEAD.match(bare)):
        return None
    if PREF_HEAD.match(bare):
        return "preferred"
    if REQ_HEAD.match(bare):
        return "required"
    return "other" if line.rstrip().endswith(":") and len(bare.split()) <= 5 else None


def analyze_job(text: str, user_skills, courses: list[dict] | None = None) -> dict:
    mode, required, preferred, all_lines = "required", {}, {}, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        all_lines.append(line)
        h = _heading(line)
        if h:
            mode = "required" if h == "other" else h
            continue
        line_mode = "preferred" if PREF_LINE.search(line) and not REQ_LINE.search(line) else "required" if REQ_LINE.search(line) else mode
        for i, s in enumerate(extract_skills(line)):
            (preferred if line_mode == "preferred" else required).setdefault(s, len(required) + len(preferred))
    for s in required:  # a skill that is required anywhere is required
        preferred.pop(s, None)
    req, pref = sorted(required, key=required.get), sorted(preferred, key=preferred.get)
    if not req and not pref:
        raise ValueError("No recognizable technical skills were found in this text. Paste the full job description.")

    have = {norm(s) for s in user_skills}
    req_have, req_missing = [s for s in req if s in have], [s for s in req if s not in have]
    pref_have, pref_missing = [s for s in pref if s in have], [s for s in pref if s not in have]
    req_m = len(req_have) / len(req) if req else None
    pref_m = len(pref_have) / len(pref) if pref else None
    score = 0.8 * req_m + 0.2 * pref_m if req and pref else (req_m if req else pref_m)

    exp, seen = [], set()
    for line in all_lines:
        for m in YEARS.finditer(line):
            key = (m.group(1), line[:60])
            if key not in seen and len(exp) < 5:
                seen.add(key)
                exp.append({"min_years": int(m.group(1)), "context": line[:140]})
    levels = [k for k, rx in LEVELS.items() if any(rx.search(l) for l in all_lines)]
    edu_lines = [l[:140] for l in all_lines if any(rx.search(l) for rx in LEVELS.values()) or re.search(r"\bdegree\b", l, re.I)][:3]

    gaps = req_missing + pref_missing
    recs = recommend_courses(gaps, have, "this role", limit=5, courses=courses, context="is requested in this job description")["courses"] if gaps else []
    return {
        "match_score": round(100 * score),
        "breakdown": {"required_match": None if req_m is None else round(100 * req_m), "preferred_match": None if pref_m is None else round(100 * pref_m)},
        "required_skills": req, "preferred_skills": pref,
        "you_have": req_have + pref_have, "should_improve": req_missing, "preferred_missing": pref_missing,
        "experience_requirements": exp, "education_requirements": {"levels": levels, "mentions": edu_lines},
        "technologies": extract_skills(text),
        "recommended_courses": [{k: r[k] for k in ("id", "title", "url", "platform", "reason")} for r in recs],
        "disclaimer": "Skills are matched by keyword. Unlabeled mentions are treated as required. Years of experience and education are listed for you to compare yourself.",
    }
