from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints

Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Line = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class ProfileData(BaseModel):
    degree: str = Field("", max_length=80)
    branch: str = Field("", max_length=120)
    institution: str = Field("", max_length=160)
    current_year: int | None = Field(None, ge=1, le=8)
    cgpa: float | None = Field(None, ge=0, le=10)
    skills: list[Tag] = Field(default_factory=list, max_length=100)
    interests: list[Tag] = Field(default_factory=list, max_length=50)
    projects: list[Line] = Field(default_factory=list, max_length=50)
    certifications: list[Line] = Field(default_factory=list, max_length=50)
    experience: list[Line] = Field(default_factory=list, max_length=50)
    career_goal: str = Field("", max_length=80)


class SkillIn(BaseModel):
    name: Tag


class SkillOut(BaseModel):
    id: int
    name: str
