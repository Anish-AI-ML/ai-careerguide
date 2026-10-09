"""Finds known skills in free text (resumes, job descriptions)."""
import re
from functools import lru_cache
from app.services.career_recommendation import load_careers, norm
from app.services.course_recommendation import load_courses
from app.services.roadmap_generator import RANK, load_ideas

# Free-text synonyms -> canonical skill. Very short/ambiguous aliases (ml, js, cv, tf) are deliberately excluded.
TEXT_ALIASES = {"scikit-learn": "machine learning", "sklearn": "machine learning", "natural language processing": "nlp",
                "amazon web services": "cloud", "aws": "cloud", "azure": "cloud", "gcp": "cloud", "google cloud": "cloud",
                "github actions": "ci/cd", "jenkins": "ci/cd", "cicd": "ci/cd", "postgresql": "sql", "postgres": "sql", "mysql": "sql",
                "nodejs": "node.js", "reactjs": "react", "k8s": "kubernetes", "hugging face": "transformers", "huggingface": "transformers",
                "keras": "deep learning", "neural network": "deep learning", "neural networks": "deep learning", "cnn": "deep learning",
                "javascript": "javascript", "data visualisation": "data visualization", "ms excel": "excel", "powerbi": "power bi"}
AMBIGUOUS = {"r"}  # single-letter skills cannot be detected reliably


@lru_cache(maxsize=1)
def vocabulary() -> dict[str, str]:
    skills = set(RANK) | set(load_ideas())
    for c in load_careers():
        skills |= {norm(s) for s in c["core"] + c["nice"]}
    for c in load_courses():
        skills |= set(c["skills"]) | set(c["prerequisites"])
    skills -= AMBIGUOUS
    vocab = {s: s for s in skills}
    vocab.update(TEXT_ALIASES)
    return vocab


@lru_cache(maxsize=512)
def _pattern(term: str) -> re.Pattern:
    return re.compile(r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#]|\.\w)", re.I)


def extract_skills(text: str) -> list[str]:
    """Canonical skills mentioned in text, in order of first appearance."""
    found: dict[str, int] = {}
    for term, canon in vocabulary().items():
        m = _pattern(term).search(text)
        if m and (canon not in found or m.start() < found[canon]):
            found[canon] = m.start()
    return sorted(found, key=found.get)
