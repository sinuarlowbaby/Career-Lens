from fastapi import APIRouter,Depends
from app.rag.query_pipeline import query_pipeline
from app.models.user import User,Resume,JobDescription
from app.db.database import get_current_user
from app.services.gap_analyzer import analyze_gap_ai


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
async def gap_analysis(user_query: str, user: User = Depends(get_current_user),top_k: int = 10):
    resume_id = user.resumes.first().id
    jd_id = user.job_descriptions.first().id
    resume_docs, jd_docs = await query_pipeline(user_query, user.id,resume_id, jd_id , top_k)

    resume_text = "\n".join([doc.page_content for doc in resume_docs])
    jd_text = "\n".join([doc.page_content for doc in jd_docs])

    gap_analysis = await analyze_gap_ai(resume_text, jd_text)
    return {"resume_docs": resume_docs, "jd_docs": jd_docs, "gap_analysis": gap_analysis}

@router.post("/auth")
async def auth():
    return {"message": "Hello World"}


