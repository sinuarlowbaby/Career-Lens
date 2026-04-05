from fastapi import APIRouter, Depends, HTTPException
from app.rag.query_pipeline import query_pipeline, gap_analysis_pipeline
from app.db.models import User,Resume,JobDescription
from app.services.auth_service import get_current_user

router = APIRouter()

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
async def gap_analysis(user: User = Depends(get_current_user)):
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


