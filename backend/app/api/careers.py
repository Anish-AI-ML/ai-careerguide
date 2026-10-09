from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import ai_rate_limit
from app.schemas.career import AnalyzeRequest, AnalyzeResponse
from app.services import career_recommendation as engine

router = APIRouter(prefix="/api", tags=["careers"])


@router.get("/careers")
def list_careers():
    return [{"id": c["id"], "name": c["name"], "required_skills": c["core"], "optional_skills": c["nice"]}
            for c in engine.load_careers()]


@router.get("/careers/{career_id}")
def get_career(career_id: str):
    for c in engine.load_careers():
        if c["id"] == career_id:
            return c
    raise HTTPException(status_code=404, detail=f"Career '{career_id}' not found")


@router.post("/career/analyze", response_model=AnalyzeResponse, dependencies=[Depends(ai_rate_limit)])
def analyze(req: AnalyzeRequest):
    profile = req.model_dump(exclude={"weights"})
    try:
        results = engine.analyze(profile, req.weights)
        weights = engine.normalize_weights(req.weights)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"top": results[0], "alternatives": results[1:5], "weights_used": weights}
