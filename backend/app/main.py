import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from contextlib import asynccontextmanager
from .api import auth, careers, chat, profile, job, progress, recommendations, resume, roadmap
from .core import security
from .database.seed import seed_skills
from .database.session import Base, SessionLocal, engine
from .models import models  # noqa: F401  (registers tables)

load_dotenv()
@asynccontextmanager
async def lifespan(_: FastAPI):
    security.secret()  # fail fast if JWT_SECRET is missing
    Base.metadata.create_all(engine)  # creates missing tables; schema.sql produces the same layout
    with SessionLocal() as db:
        seed_skills(db)
    yield


app = FastAPI(title="AI CareerGuide API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


def _err(status: int, code: str, message: str, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details}})


@app.exception_handler(HTTPException)
async def http_exc(_: Request, exc: HTTPException):
    return _err(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exc(_: Request, exc: RequestValidationError):
    details = [{"field": ".".join(map(str, e["loc"][1:])), "message": e["msg"]} for e in exc.errors()]
    return _err(422, "validation_error", "Invalid request body", details)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    return _err(500, "internal_error", "Something went wrong")


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(careers.router)
app.include_router(recommendations.router)
app.include_router(roadmap.router)
app.include_router(resume.router)
app.include_router(job.router)
app.include_router(chat.router)
app.include_router(progress.router)
