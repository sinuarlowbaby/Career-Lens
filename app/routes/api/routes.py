from fastapi import APIRouter, Depends, HTTPException
from app.rag.query_pipeline import query_pipeline, gap_analysis_pipeline
from app.db.models import User,Resume,JobDescription
from app.services.auth_service import get_current_user
from pydantic import BaseModel
from typing import Optional
from app.services.gap_analyzer import analyze_gap_ai

router = APIRouter()

class GapAnalysisRequest(BaseModel):
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.post("/chat")
async def chat():
    return {"message": "Hello World"}

@router.post("/ats")
async def ats():
    return {"message": "Hello World"}

@router.post("/interview")
async def interview():
    return {"message": "Hello World"}

@router.post("/gap_analysis")
async def gap_analysis(payload: GapAnalysisRequest = None, user: User = Depends(get_current_user)):
    # If the user edited the text directly in the UI, use that text directly
    if payload and payload.resume_text and payload.jd_text:
        # Note: analyze_gap_ai truncates to 6000 and 3000 characters internally to prevent LLM overflow
        result = await analyze_gap_ai(payload.resume_text, payload.jd_text)
        return {"gap_analysis": result}

    if not user.resumes or len(user.resumes) == 0:
        raise HTTPException(status_code=400, detail="No resume uploaded. Please upload a resume first.")
    if not user.job_descriptions or len(user.job_descriptions) == 0:
        raise HTTPException(status_code=400, detail="No job description uploaded. Please upload a job description first.")
        
    latest_resume = sorted(user.resumes, key=lambda r: r.created_at, reverse=True)[0]
    latest_jd = sorted(user.job_descriptions, key=lambda j: j.created_at, reverse=True)[0]
    
    resume_id = latest_resume.id
    jd_id = latest_jd.id
    
    result = await gap_analysis_pipeline(user.id, resume_id, jd_id)
    return result

@router.post("/auth")
async def auth():
    return {"message": "Hello World"}