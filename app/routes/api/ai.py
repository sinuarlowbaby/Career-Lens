from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.services.chat_service import chat_with_ai
from app.services.resume_analyze import analyze_resume
from app.services.gap_analyzer import analyze_skill_gap
from app.services.interview_service import (
    create_session,
    get_questions,
    evaluate_user_answer
)

router = APIRouter()


@router.post("/chat")
async def chat(data: dict):
    return await chat_with_ai(data["message"])


@router.post("/resume-analyze")
async def resume_analysis(data: dict):
    return await analyze_resume(data["resume"], data["job"])


@router.post("/gap-analysis")
async def gap_analysis(data: dict):
    return await analyze_skill_gap(data["resume"], data["job"])


@router.post("/interview/start")
def start_interview(data: dict, db: Session = Depends(get_db)):
    return create_session(db, data["user_id"], data["role"])


@router.post("/interview/questions")
async def questions(data: dict):
    return await get_questions(data["role"])


@router.post("/interview/evaluate")
async def evaluate(data: dict, db: Session = Depends(get_db)):
    return await evaluate_user_answer(
        db,
        data["session_id"],
        data["answer"]
    )