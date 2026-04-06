from fastapi import APIRouter, Depends, HTTPException
from app.rag.query_pipeline import query_pipeline, gap_analysis_pipeline
from app.db.models import User, Resume, JobDescription
from app.services.auth_service import get_current_user
from app.db.session import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal
from app.services.gap_analyzer import analyze_gap_ai
from app.services.ats_score import analyze_ats_ai
from app.services.chat_service import generate_ai_response
from app.services.interview_service import (
    start_interview_session,
    submit_answer,
    get_next_question,
    finish_session,
)

router = APIRouter()


# ── Generic request/response models ──────────────────────────────────────────

class GapAnalysisRequest(BaseModel):
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None


class AtsRequest(BaseModel):
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    prompt: str
    system: Optional[str] = "You are an AI career coach"
    history: Optional[list[ChatMessage]] = []


# ── Interview request/response models ────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    topic: str   # e.g. "Behavioural", "System Design", "DSA & Python"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None


class InterviewAnswerRequest(BaseModel):
    session_id: int
    question_text: str    # exact question that was shown to the user
    answer: str


class InterviewNextRequest(BaseModel):
    session_id: int


class InterviewFinishRequest(BaseModel):
    session_id: int


# ── Utility endpoints ─────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {"status": "ok"}


# ── General chat ──────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(payload: ChatRequest):
    try:
        result = await generate_ai_response(payload.prompt, payload.system, payload.history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── ATS Score ────────────────────────────────────────────────────────────────

@router.post("/ats")
async def ats(payload: AtsRequest = None, user: User = Depends(get_current_user)):
    if payload and payload.resume_text and payload.jd_text:
        result = await analyze_ats_ai(payload.resume_text, payload.jd_text)
        return {"ats_analysis": result}

    raise HTTPException(status_code=400, detail="Please provide resume_text and jd_text in the payload.")


# ── Gap Analysis ─────────────────────────────────────────────────────────────

@router.post("/gap_analysis")
async def gap_analysis(payload: GapAnalysisRequest = None, user: User = Depends(get_current_user)):
    # If the user edited the text directly in the UI, use that text directly
    if payload and payload.resume_text and payload.jd_text:
        result = await analyze_gap_ai(payload.resume_text, payload.jd_text)
        return {"gap_analysis": result}

    if not user.resumes or len(user.resumes) == 0:
        raise HTTPException(status_code=400, detail="No resume uploaded. Please upload a resume first.")
    if not user.job_descriptions or len(user.job_descriptions) == 0:
        raise HTTPException(status_code=400, detail="No job description uploaded. Please upload a job description first.")

    latest_resume = sorted(user.resumes, key=lambda r: r.created_at, reverse=True)[0]
    latest_jd = sorted(user.job_descriptions, key=lambda j: j.created_at, reverse=True)[0]

    result = await gap_analysis_pipeline(user.id, latest_resume.id, latest_jd.id)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# MOCK INTERVIEW — 4 structured endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/interview/start")
async def interview_start(
    payload: InterviewStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Start a new interview session.
    - Generates 5 questions tailored to the user's resume, JD, topic, and difficulty.
    - Returns session_id and the first question.
    """
    # Resolve resume and JD text: payload overrides > latest DB record
    resume_text = payload.resume_text or ""
    jd_text = payload.jd_text or ""

    if not resume_text and user.resumes:
        latest = sorted(user.resumes, key=lambda r: r.created_at, reverse=True)[0]
        resume_text = latest.content or ""

    if not jd_text and user.job_descriptions:
        latest = sorted(user.job_descriptions, key=lambda j: j.created_at, reverse=True)[0]
        jd_text = latest.content or ""

    result = await start_interview_session(
        db=db,
        user_id=user.id,
        topic=payload.topic,
        difficulty=payload.difficulty,
        resume_text=resume_text,
        jd_text=jd_text,
    )
    return result


@router.post("/interview/answer")
async def interview_answer(
    payload: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Submit an answer for the current question.
    - Evaluates the answer with the LLM.
    - Persists QALog to the database.
    - Returns evaluation: score, strengths, improvements, hint, and follow-up flag.
    """
    if not payload.answer or not payload.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")

    result = await submit_answer(
        db=db,
        session_id=payload.session_id,
        question_text=payload.question_text,
        answer=payload.answer,
    )
    return result


@router.post("/interview/next")
async def interview_next(
    payload: InterviewNextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get the next question.
    - If previous answer triggered a follow-up: returns a contextual follow-up question.
    - Otherwise: returns the next base question from the pre-generated list.
    - Returns {"done": true} when all questions are exhausted.
    """
    result = await get_next_question(db=db, session_id=payload.session_id)
    return result


@router.post("/interview/finish")
async def interview_finish(
    payload: InterviewFinishRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Complete the interview session.
    - Computes overall score as the average of all QALog scores.
    - Marks Interview record as completed.
    - Returns the final overall score and a per-question breakdown.
    """
    result = finish_session(db=db, session_id=payload.session_id)
    return result


@router.post("/auth")
async def auth():
    return {"message": "Hello World"}