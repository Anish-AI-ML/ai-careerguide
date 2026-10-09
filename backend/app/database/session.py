import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()


def _url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./careerguide.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


URL = _url()
_kw: dict = {}
if URL.startswith("sqlite"):
    _kw["connect_args"] = {"check_same_thread": False}
    if URL in ("sqlite://", "sqlite:///:memory:"):
        _kw["poolclass"] = StaticPool
else:
    _kw["pool_pre_ping"] = True
    if "pooler" in URL or os.getenv("DB_PGBOUNCER") == "1":
        # PgBouncer in transaction mode (e.g. Supabase pooler) cannot use server-side prepared statements.
        _kw["connect_args"] = {"prepare_threshold": None}

engine = create_engine(URL, **_kw)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
