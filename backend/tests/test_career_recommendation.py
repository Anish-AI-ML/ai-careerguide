import pytest
from app.services.career_recommendation import analyze, normalize_weights

PROFILE = {
    "education": {"degree": "B.E.", "branch": "Computer Science (AI & ML)", "cgpa": 8.5},
    "skills": ["Python", "ML", "TensorFlow", "SQL", "Git", "Deep Learning"],
    "interests": ["Artificial Intelligence", "Machine Learning"],
    "projects": [{"title": "Traffic prediction", "description": "python machine learning model with tensorflow"}],
    "certifications": ["Deep Learning Specialization"],
    "experience": ["ML internship"],
    "career_goal": "AI/ML Engineer",
}

def test_top_is_ai_ml_and_scores_in_range():
    r = analyze(PROFILE)
    assert r[0]["career"] == "AI/ML Engineer" and r[0]["goal_bonus"] == 5
    assert all(0 <= x["match_score"] <= 100 for x in r)
    ai = next(x for x in r if x["career"] == "AI/ML Engineer")
    assert ai["is_goal"] and "mlops" in ai["skill_gaps"]

def test_deterministic():
    assert analyze(PROFILE) == analyze(PROFILE)

def test_weights_configurable_and_validated():
    assert abs(sum(normalize_weights({"skills": 0.9}).values()) - 1) < 1e-9
    with pytest.raises(ValueError):
        normalize_weights({"skills": -1})
    only_interest = analyze({**PROFILE, "career_goal": ""}, {"skills": 0, "interests": 1, "education": 0, "projects": 0, "experience": 0})
    assert only_interest[0]["breakdown"]["interests"] == only_interest[0]["match_score"]

def test_empty_profile_does_not_crash():
    assert analyze({})[0]["match_score"] >= 0
