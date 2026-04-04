from fastapi import APIRouter, HTTPException,Depends
from app.llm.llm_client import generate_response
from pydantic import BaseModel, Field
from app.rag.ingestion_pipeline import ingestion_pipeline
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.db.models import User, Resume, JobDescription



router = APIRouter(prefix="/ai", tags=["ai"])


class Prompt(BaseModel):
    prompt: str = Field(..., description="Prompt to send to the AI", min_length=1, max_length=4000)


class AskResponse(BaseModel):
    response: str


@router.post("/ask", response_model=AskResponse)
async def ask_ai(body: Prompt):
    # Bug fix: was passing the whole Pydantic object — must pass body.prompt (the string)
    result = await generate_response(body.prompt)
    return AskResponse(response=result)



@router.post("/embed_docs", response_model=AskResponse)
async def embed_docs(
    db: Session = Depends(get_db), # Don't forget Depends() for your DB session
    user_id: str = Depends(get_current_user)
):
    # 1. Fetch the entire row efficiently (only 2 queries instead of 4)
    resume = db.query(Resume).filter(Resume.user_id == user_id).first()
    jd = db.query(JobDescription).filter(JobDescription.user_id == user_id).first()

    # 2. Safety Check: Ensure the data actually exists before trying to access .content
    if not resume or not jd:
        raise HTTPException(
            status_code=400, 
            detail="You must upload both a Resume and a Job Description first."
        )

    result = await ingestion_pipeline(
        db=db, 
        user_id=user_id, 
        resume_content=resume.content, 
        job_description_content=jd.content, 
        resume_id=resume.id, 
        jd_id=jd.id
    )
    return {"status": "success", "message": f"Successfully processed {result['chunks_stored']} chunks."} 

