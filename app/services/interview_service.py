import json
import re
from sqlalchemy.orm import Session
from app.db.models import Interview, QALog
from app.services.chat_service import generate_ai_response


def create_session(db: Session, user_id: int, role: str = "General"):
    interview = Interview(user_id=user_id)
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


async def generate_questions(role: str):
    prompt = f"""
    Generate 5 interview questions for {role}
    """

    return await generate_ai_response(prompt)


async def evaluate_answer(db: Session, session_id: int, answer: str):
    prompt = f"""
    Evaluate this answer:

    {answer}

    Return ONLY valid JSON with exactly these keys:
    {"score": 8, "feedback": "...", "improvements": "..."}
    """

    ai_result = await generate_ai_response(prompt)
    ai_text = ai_result.get("response", "{}")

    try:
        match = re.search(r"\{.*\}", ai_text, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else {}
        score = float(parsed.get("score", 5.0))
    except Exception:
        score = 5.0

    db_answer = QALog(
        interview_id=session_id,
        user_answer=answer,
        ai_feedback=ai_text,
        score=score
    )
    db.add(db_answer)
    db.commit()

    return ai_result