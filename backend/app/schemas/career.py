from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints

Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class Education(BaseModel):
    degree: str = Field("", max_length=80)
    branch: str = Field("", max_length=120)
    institution: str = Field("", max_length=160)
    year: int | None = Field(None, ge=1, le=8)
    cgpa: float | None = Field(None, ge=0, le=10)


class AnalyzeRequest(BaseModel):
    education: Education = Education()
    skills: list[Tag] = Field(default_factory=list, max_length=100)
    interests: list[Tag] = Field(default_factory=list, max_length=50)
    projects: list[str | dict[str, str]] = Field(default_factory=list, max_length=50)
    certifications: list[str] = Field(default_factory=list, max_length=50)
    experience: list[str] = Field(default_factory=list, max_length=50)
    career_goal: str = Field("", max_length=80)  # empty / "not sure" => rank all careers
    weights: dict[str, float] | None = None


class CareerMatch(BaseModel):
    id: str
    career: str
    match_score: int = Field(ge=0, le=100)
    reason: str
    strengths: list[str]
    skill_gaps: list[str]
    breakdown: dict[str, int]
    is_goal: bool
    goal_bonus: int
    disclaimer: str


class AnalyzeResponse(BaseModel):
    top: CareerMatch
    alternatives: list[CareerMatch]
    weights_used: dict[str, float]
