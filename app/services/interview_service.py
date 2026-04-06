"""
interview_service.py
Production-grade mock interview session engine.

Session lifecycle:
  1. start_interview_session()   → create DB row, generate 5 questions, return Q1
  2. submit_answer()             → evaluate answer, save QALog, check for follow-up
  3. get_next_question()         → return follow-up OR next base question
  4. finish_session()            → compute final score, mark session complete

Session context is stored in an in-process dict keyed by session_id.
(Move to Redis for multi-worker production deployments.)
"""

import json
import logging
from sqlalchemy.orm import Session
from app.db.models import Interview, QALog, InterviewStatus
from app.llm.question_generator import (
    generate_interview_questions,
    generate_followup_question,
    InterviewQuestion,
)
from app.llm.answer_evaluation import evaluate_answer, AnswerEvaluation

logger = logging.getLogger(__name__)

# ── In-process session cache ─────────────────────────────────────────────────
# Structure per session_id:
# {
#   "questions": [{"question": str, "category": str, "difficulty": str}, ...],
#   "base_q_index": int,            # index into questions[] for the NEXT base question
#   "question_number": int,         # 1-based counter shown to the user
#   "total_questions": int,         # dynamically updated if follow-ups are added
#   "needs_followup": bool,
#   "followup_reason": str,
#   "prev_question": str,
#   "prev_answer": str,
#   "last_was_followup": bool,      # prevent chaining follow-ups
#   "followups_used": int,          # max 2 follow-ups per session
#   "topic": str,
#   "difficulty": str,
#   "resume_text": str,
#   "jd_text": str,
# }
_SESSION_CACHE: dict[int, dict] = {}

MAX_BASE_QUESTIONS = 5
MAX_FOLLOWUPS = 2


# ── Start a new interview session ────────────────────────────────────────────

async def start_interview_session(
    db: Session,
    user_id: int,
    topic: str,
    difficulty: str,
    resume_text: str,
    jd_text: str,
) -> dict:
    """
    Create an Interview DB row, generate 5 base questions, cache session context,
    and return the first question.
    """
    # 1. Create DB record
    interview = Interview(user_id=user_id, status=InterviewStatus.in_progress)
    db.add(interview)
    db.commit()
    db.refresh(interview)
    session_id = interview.id
    logger.info(f"[Interview] Started session_id={session_id} topic={topic!r} difficulty={difficulty!r}")

    # 2. Generate 5 base questions from LLM
    questions: list[InterviewQuestion] = await generate_interview_questions(
        resume_text=resume_text,
        jd_text=jd_text,
        topic=topic,
        difficulty=difficulty,
    )

    # 3. Serialize & cache session context
    _SESSION_CACHE[session_id] = {
        "questions": [q.model_dump() for q in questions],
        "base_q_index": 1,           # Q1 is being returned now, next base = index 1
        "question_number": 1,
        "total_questions": MAX_BASE_QUESTIONS,
        "needs_followup": False,
        "followup_reason": "",
        "prev_question": questions[0].question,
        "prev_answer": "",
        "last_was_followup": False,
        "followups_used": 0,
        "topic": topic,
        "difficulty": difficulty,
        "resume_text": resume_text,
        "jd_text": jd_text,
    }

    first_q = questions[0]
    logger.info(f"[Interview] session_id={session_id} generated {len(questions)} questions, serving Q1")

    return {
        "session_id": session_id,
        "question_number": 1,
        "total_questions": MAX_BASE_QUESTIONS,
        "question": first_q.question,
        "category": first_q.category,
        "difficulty": first_q.difficulty,
        "is_followup": False,
        "followup_reason": None,
    }


# ── Submit an answer and evaluate it ─────────────────────────────────────────

async def submit_answer(
    db: Session,
    session_id: int,
    question_text: str,
    answer: str,
) -> dict:
    """
    Evaluate the candidate's answer, persist to QALog, update session context
    with the follow-up decision.
    """
    ctx = _SESSION_CACHE.get(session_id)
    if not ctx:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Interview session not found or expired.")

    question_number = ctx["question_number"]
    logger.info(f"[Interview] session_id={session_id} evaluating Q{question_number}")

    # 1. Evaluate with LLM
    evaluation: AnswerEvaluation = await evaluate_answer(
        question=question_text,
        answer=answer,
        topic=ctx["topic"],
        difficulty=ctx["difficulty"],
        question_number=question_number,
        total_questions=ctx["total_questions"],
        resume_text=ctx["resume_text"],
        jd_text=ctx["jd_text"],
    )

    # 2. Persist QALog
    qa_log = QALog(
        interview_id=session_id,
        question=question_text,
        user_answer=answer,
        ai_feedback=json.dumps({
            "overall_feedback": evaluation.overall_feedback,
            "strengths": evaluation.strengths,
            "improvements": evaluation.improvements,
            "ideal_answer_hint": evaluation.ideal_answer_hint,
        }),
        score=evaluation.score,
    )
    db.add(qa_log)
    db.commit()
    logger.info(f"[Interview] session_id={session_id} Q{question_number} score={evaluation.score}")

    # 3. Decide if follow-up should fire
    can_followup = (
        evaluation.needs_followup
        and not ctx["last_was_followup"]          # never chain follow-ups
        and ctx["followups_used"] < MAX_FOLLOWUPS  # budget cap
        and ctx["base_q_index"] < MAX_BASE_QUESTIONS  # at least one base Q remains
    )

    # 4. Update session context
    ctx["needs_followup"] = can_followup
    ctx["followup_reason"] = evaluation.followup_reason if can_followup else ""
    ctx["prev_question"] = question_text
    ctx["prev_answer"] = answer
    if can_followup:
        ctx["total_questions"] += 1  # add 1 slot for the follow-up

    return {
        "score": evaluation.score,
        "strengths": evaluation.strengths,
        "improvements": evaluation.improvements,
        "ideal_answer_hint": evaluation.ideal_answer_hint,
        "overall_feedback": evaluation.overall_feedback,
        "needs_followup": can_followup,
    }


# ── Get the next question ─────────────────────────────────────────────────────

async def get_next_question(db: Session, session_id: int) -> dict:
    """
    Return the next question. If the previous answer triggered a follow-up,
    generate and return that. Otherwise return the next base question.
    Returns {"done": True} when all questions are exhausted.
    """
    ctx = _SESSION_CACHE.get(session_id)
    if not ctx:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Interview session not found or expired.")

    # Advance question counter
    ctx["question_number"] += 1
    q_number = ctx["question_number"]

    # ── FOLLOW-UP BRANCH ─────────────────────────────────────────────────────
    if ctx["needs_followup"]:
        logger.info(f"[Interview] session_id={session_id} generating follow-up for Q{q_number}")
        followup = await generate_followup_question(
            topic=ctx["topic"],
            difficulty=ctx["difficulty"],
            prev_question=ctx["prev_question"],
            prev_answer=ctx["prev_answer"],
            weakness_area=ctx["followup_reason"],
        )
        ctx["needs_followup"] = False
        ctx["last_was_followup"] = True
        ctx["followups_used"] += 1
        ctx["prev_question"] = followup.question

        return {
            "session_id": session_id,
            "question_number": q_number,
            "total_questions": ctx["total_questions"],
            "question": followup.question,
            "category": ctx["topic"],
            "difficulty": ctx["difficulty"],
            "is_followup": True,
            "followup_reason": followup.reason,
            "done": False,
        }

    # ── BASE QUESTION BRANCH ─────────────────────────────────────────────────
    ctx["last_was_followup"] = False
    base_idx = ctx["base_q_index"]

    if base_idx >= MAX_BASE_QUESTIONS:
        # Session is complete
        logger.info(f"[Interview] session_id={session_id} all questions exhausted")
        return {"done": True, "session_id": session_id}

    next_q = ctx["questions"][base_idx]
    ctx["base_q_index"] += 1
    ctx["prev_question"] = next_q["question"]

    return {
        "session_id": session_id,
        "question_number": q_number,
        "total_questions": ctx["total_questions"],
        "question": next_q["question"],
        "category": next_q["category"],
        "difficulty": next_q["difficulty"],
        "is_followup": False,
        "followup_reason": None,
        "done": False,
    }


# ── Finish the session ────────────────────────────────────────────────────────

def finish_session(db: Session, session_id: int) -> dict:
    """
    Compute average score from all QALog rows, update Interview record,
    clean up session cache, and return the final summary.
    """
    interview = db.query(Interview).filter(Interview.id == session_id).first()
    if not interview:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Aggregate scores
    logs = db.query(QALog).filter(QALog.interview_id == session_id).all()
    scores = [log.score for log in logs if log.score is not None]
    overall_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    # Mark completed
    import datetime
    interview.overall_score = overall_score
    interview.status = InterviewStatus.completed
    interview.completed_at = datetime.datetime.utcnow()
    db.commit()

    # Build per-question breakdown for final results panel
    breakdown = []
    for i, log in enumerate(logs):
        try:
            feedback = json.loads(log.ai_feedback or "{}")
        except Exception:
            feedback = {}
        breakdown.append({
            "question_number": i + 1,
            "question": log.question,
            "answer": log.user_answer,
            "score": log.score,
            "strengths": feedback.get("strengths", []),
            "improvements": feedback.get("improvements", []),
            "ideal_answer_hint": feedback.get("ideal_answer_hint", ""),
        })

    # Clean up in-memory cache
    _SESSION_CACHE.pop(session_id, None)
    logger.info(f"[Interview] session_id={session_id} finished overall_score={overall_score}")

    return {
        "session_id": session_id,
        "overall_score": overall_score,
        "total_questions_answered": len(logs),
        "breakdown": breakdown,
    }