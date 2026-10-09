from pydantic import Field
from pydantic import BaseModel
from app.schemas.career import AnalyzeRequest


class CourseRequest(AnalyzeRequest):
    career_id: str | None = Field(None, max_length=60)
    exclude: list[str] = Field(default_factory=list, max_length=200)
    limit: int = Field(6, ge=1, le=20)


class CourseRec(BaseModel):
    id: str
    title: str
    platform: str
    provider: str
    skills: list[str]
    difficulty: str
    duration_hours: float
    rating: float | None
    url: str
    prerequisites: list[str]
    free: bool
    score: float
    covers: list[str]
    missing_prerequisites: list[str]
    reason: str


class CourseResponse(BaseModel):
    career: str
    career_id: str
    match_score: int
    courses: list[CourseRec]
    uncovered_skills: list[str]
