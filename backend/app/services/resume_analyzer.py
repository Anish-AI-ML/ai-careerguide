"""Heuristic resume parsing + transparent scoring. Output is guidance; extraction can be imperfect."""
import re
from app.services import career_recommendation as eng
from app.services.course_recommendation import pretty, recommend_courses
from app.services.roadmap_generator import load_ideas
from app.services.skill_extraction import extract_skills

HEADS = {
    "education": {"education", "academic background", "academics", "academic qualifications"},
    "experience": {"experience", "work experience", "professional experience", "internships", "internship experience", "employment", "work history"},
    "projects": {"projects", "academic projects", "personal projects", "key projects", "selected projects"},
    "skills": {"skills", "technical skills", "core competencies", "technologies", "tech stack", "skills & tools"},
    "certifications": {"certifications", "certificates", "courses", "licenses", "training", "licenses & certifications"},
    "achievements": {"achievements", "awards", "hackathons", "honors", "extracurricular", "activities", "publications"},
}
VERBS = {"built", "developed", "designed", "implemented", "led", "created", "deployed", "trained", "optimized", "optimised", "improved",
         "reduced", "increased", "automated", "analyzed", "analysed", "engineered", "integrated", "delivered", "managed", "collaborated",
         "researched", "achieved", "launched", "architected", "evaluated", "migrated", "tested", "presented", "mentored", "produced"}
BULLET = re.compile(r"^[\u2022\u25cf\u25aa\-\*\u2013\u00b7]\s*")


def split_sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"header": []}
    cur = "header"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        key = re.sub(r"[^a-z& ]", "", line.lower()).strip()
        found = next((k for k, v in HEADS.items() if key in v), None) if len(line) <= 40 else None
        if found:
            cur = found
            out.setdefault(cur, [])
        else:
            out.setdefault(cur, []).append(BULLET.sub("", line))
    return out


def guess_name(header: list[str]) -> str | None:
    for line in header[:4]:
        if re.fullmatch(r"[A-Za-z][A-Za-z.'\- ]{2,40}", line) and 2 <= len(line.split()) <= 4:
            return line.strip()
    return None


def _titles(lines: list[str], cap: int = 8) -> list[str]:
    """Entry titles: short lines; falls back to the first lines when everything is bullets."""
    t = [l for l in lines if len(l) <= 90]
    return (t or lines)[:cap]


def _metrics(text: str) -> int:
    t = re.sub(r"\b(?:19|20)\d{2}\b", "", text)
    return len(re.findall(r"\d+(?:\.\d+)?\s?%|\b\d[\d,]{2,}\b|\b\d+(?:\.\d+)?\s?x\b", t))


def quality_score(sections: dict, text: str, skills: list[str]) -> tuple[int, dict]:
    words = len(text.split())
    verbs = len({w for w in re.findall(r"[a-z]+", text.lower()) if w in VERBS})
    metrics = _metrics(text)
    length_pts = 15 if 200 <= words <= 900 else 15 * max(0.0, 1 - (200 - words) / 200) if words < 200 else 15 * max(0.0, 1 - (words - 900) / 600)
    comp = {
        "sections": (8 * bool(sections.get("education")) + 8 * bool(sections.get("skills")) + 8 * bool(sections.get("projects"))
                     + 6 * bool(sections.get("experience") or sections.get("certifications")), 30),
        "quantified_impact": (20 * min(1, metrics / 5), 20),
        "skills_breadth": (20 * min(1, len(skills) / 12), 20),
        "length": (length_pts, 15),
        "action_verbs": (15 * min(1, verbs / 6), 15),
    }
    breakdown = {k: {"points": round(v[0], 1), "max": v[1]} for k, v in comp.items()}
    return round(sum(v[0] for v in comp.values())), breakdown


def analyze_resume(text: str, career: dict, courses: list[dict] | None = None) -> dict:
    sec = split_sections(text)
    sec_text = {k: " ".join(v) for k, v in sec.items()}
    all_skills = extract_skills(text)
    listed = extract_skills(sec_text.get("skills", "")) or all_skills
    evidence_text = f"{sec_text.get('projects', '')} {sec_text.get('experience', '')}"
    technologies = extract_skills(evidence_text)
    score, breakdown = quality_score(sec, text, all_skills)

    c = eng.normalized_career(career)
    have = set(all_skills)
    skill_m, got_core, missing_core = eng.skill_match(have, c)
    proj_m = eng.evidence(sec_text.get("projects", ""), c, 3)
    exp_m = eng.evidence(f"{sec_text.get('experience', '')} {sec_text.get('certifications', '')}", c, 2)
    overall = 0.5 * skill_m + 0.3 * proj_m + 0.2 * exp_m
    pct = lambda x: round(100 * x)  # noqa: E731

    words, metrics = len(text.split()), _metrics(text)
    n_proj, n_exp = len(_titles(sec.get("projects", []))), len(_titles(sec.get("experience", [])))
    strengths = []
    if len(all_skills) >= 8:
        strengths.append(f"Lists {len(all_skills)} recognizable technical skills")
    if got_core:
        strengths.append(f"Covers core {career['name']} skills: {', '.join(pretty(s) for s in got_core[:5])}")
    if sec.get("projects") and n_proj >= 2:
        strengths.append(f"Includes {n_proj} project entries")
    if metrics >= 3:
        strengths.append("Quantifies results with numbers or percentages")
    if sec.get("experience"):
        strengths.append("Has an experience or internship section")

    ats = []
    for key, label in (("education", "Education"), ("skills", "Skills"), ("projects", "Projects")):
        if not sec.get(key):
            ats.append(f"Add a clearly labeled '{label}' section with a standard heading so ATS parsers can find it.")
    if not sec.get("experience"):
        ats.append("Add an 'Experience' section (internships, freelance or open-source work count) if you have any.")
    if words < 200:
        ats.append("The resume is quite short; add detail about projects and impact.")
    elif words > 900:
        ats.append("The resume is long; aim for one or two pages by trimming older or less relevant details.")
    if metrics < 3:
        ats.append("Quantify results (e.g. accuracy, users, records processed, time saved) so impact is measurable.")
    if len({w for w in re.findall(r"[a-z]+", text.lower()) if w in VERBS}) < 4:
        ats.append("Start bullet points with strong action verbs such as built, deployed, optimized or reduced.")
    ats.append("Use a simple single-column layout, standard fonts and plain text headings; avoid tables, icons and text in images.")

    ideas = load_ideas()
    project_suggestions = [ideas[s][0] for s in missing_core if s in ideas][:3]
    if not sec.get("projects"):
        project_suggestions.insert(0, f"Add 2-3 projects relevant to {career['name']} with the technologies and results for each.")
    recs = recommend_courses(missing_core, have, career["name"], limit=3, courses=courses)["courses"] if missing_core else []

    return {
        "name": guess_name(sec["header"]),
        "sections_found": [k for k in sec if k != "header" and sec[k]],
        "extracted": {"education": sec.get("education", [])[:6], "skills": listed, "technologies": technologies,
                      "projects": _titles(sec.get("projects", [])), "experience": _titles(sec.get("experience", [])),
                      "certifications": sec.get("certifications", [])[:8]},
        "resume_score": score, "score_breakdown": breakdown,
        "target": {"career": career["name"], "career_id": career["id"]},
        "role_match": {"skills": pct(skill_m), "projects": pct(proj_m), "experience": pct(exp_m), "overall": pct(overall)},
        "strengths": strengths,
        "missing_keywords": [s for s in c["core"] + c["nice"] if s not in have],
        "technical_skill_gaps": missing_core,
        "recommended_courses": [{k: r[k] for k in ("id", "title", "url", "platform", "reason")} for r in recs],
        "project_suggestions": project_suggestions,
        "ats_suggestions": ats,
        "disclaimer": "Automated heuristic analysis. Check the extracted details, and treat scores as guidance rather than a hiring prediction.",
    }
