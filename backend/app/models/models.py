import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, Boolean, Text, DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

JSONList = JSON().with_variant(JSONB(), "postgresql")
now = lambda: datetime.now(timezone.utc)  # noqa: E731


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    profile: Mapped["Profile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    degree: Mapped[str] = mapped_column(String(80), default="")
    branch: Mapped[str] = mapped_column(String(120), default="")
    institution: Mapped[str] = mapped_column(String(160), default="")
    current_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    interests: Mapped[list] = mapped_column(JSONList, default=list)
    projects: Mapped[list] = mapped_column(JSONList, default=list)
    certifications: Mapped[list] = mapped_column(JSONList, default=list)
    experience: Mapped[list] = mapped_column(JSONList, default=list)
    career_goal: Mapped[str] = mapped_column(String(80), default="")  # "" = "I'm not sure yet"
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    user: Mapped[User] = relationship(back_populates="profile")


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_key: Mapped[str] = mapped_column(String(60), unique=True)  # lowercase, for dedupe
    name: Mapped[str] = mapped_column(String(60))
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)


class UserSkill(Base):
    __tablename__ = "user_skills"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    level: Mapped[int] = mapped_column(Integer, default=1)


class Roadmap(Base):
    __tablename__ = "roadmaps"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    career_id: Mapped[str] = mapped_column(String(60))
    career_name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    items: Mapped[list["RoadmapItem"]] = relationship(back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapItem.phase")


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True)
    phase: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(160))
    skills: Mapped[list] = mapped_column(JSONList, default=list)
    est_weeks: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[str] = mapped_column(String(20))
    courses: Mapped[list] = mapped_column(JSONList, default=list)
    projects: Mapped[list] = mapped_column(JSONList, default=list)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    roadmap: Mapped[Roadmap] = relationship(back_populates="items")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analysis"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    career_id: Mapped[str] = mapped_column(String(60))
    score: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict] = mapped_column(JSONList)  # analysis only; the PDF and raw text are never stored
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class JobAnalysis(Base):
    __tablename__ = "job_analysis"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120), default="")
    match_score: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict] = mapped_column(JSONList)  # extracted analysis only; the pasted text is not stored
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    session: Mapped[ChatSession] = relationship(back_populates="messages")


class UserCourse(Base):
    __tablename__ = "user_courses"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(60), primary_key=True)  # id from data/courses.json
    status: Mapped[str] = mapped_column(String(20))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    readiness: Mapped[int] = mapped_column(Integer)
    skill_count: Mapped[int] = mapped_column(Integer)
    roadmap_percent: Mapped[int] = mapped_column(Integer)
    courses_completed: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
