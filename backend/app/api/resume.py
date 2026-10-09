import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import ai_rate_limit, current_user
from app.api.profile import profile_dict
from app.api.recommendations import pick_target
from app.database.session import get_db
from ..models.models import ResumeAnalysis, User
from app.services import career_recommendation as engine
from app.services.pdf_text import PdfError, extract_pdf_text
from app.services.resume_analyzer import analyze_resume

router = APIRouter(prefix="/api/resume", tags=["resume"])
PDF_TYPES = {"application/pdf", "application/x-pdf"}


def _max_bytes() -> int:
    return int(float(os.getenv("RESUME_MAX_MB", "5")) * 1024 * 1024)


@router.post("/analyze", dependencies=[Depends(ai_rate_limit)])
def analyze(request: Request, file: UploadFile = File(...), career_id: str | None = Form(None),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    limit = _max_bytes()
    cl = request.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > limit + 65536:
        raise HTTPException(status_code=413, detail=f"File too large (max {limit // (1024 * 1024)} MB)")
    if not (file.filename or "").lower().endswith(".pdf") or (file.content_type or "") not in PDF_TYPES:
        raise HTTPException(status_code=415, detail="Please upload a PDF file")
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File too large (max {limit // (1024 * 1024)} MB)")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="This file is not a valid PDF")
    try:
        text = extract_pdf_text(data)
    except PdfError as e:
        raise HTTPException(status_code=422, detail=str(e))

    careers = engine.load_careers()
    if career_id:
        target = next((c for c in careers if c["id"] == career_id), None)
        if not target:
            raise HTTPException(status_code=404, detail=f"Career '{career_id}' not found")
    else:
        profile = profile_dict(db, user)
        if not profile:
            raise HTTPException(status_code=422, detail="Choose a target career or complete your profile first")
        tid = pick_target(engine.analyze(profile), None)["id"]
        target = next(c for c in careers if c["id"] == tid)

    result = analyze_resume(text, target)
    row = ResumeAnalysis(user_id=user.id, career_id=target["id"], score=result["resume_score"], result=result)
    db.add(row)
    db.commit()
    return {"id": str(row.id), **result}


@router.get("/latest")
def latest(user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.scalar(select(ResumeAnalysis).where(ResumeAnalysis.user_id == user.id).order_by(ResumeAnalysis.created_at.desc()))
    if not row:
        raise HTTPException(status_code=404, detail="No resume analyzed yet")
    return {"id": str(row.id), **row.result}
