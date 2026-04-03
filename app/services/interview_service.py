from sqlalchemy.orm import Session
from app.models import InterviewSession, Answer
from app.services.chat_service import call_qwen


def create_session(db: Session, user_id: int, role: str):
    session = InterviewSession(user_id=user_id, role=role)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


async def generate_questions(role: str):
    prompt = f"""
    Generate 5 technical interview questions for {role}
    """

    return await call_qwen(prompt)


async def evaluate_answer(db: Session, session_id: int, answer: str):
    prompt = f"""
    Evaluate this answer:

    {answer}

    Return:
    - score (0-10)
    - feedback
    - improvements
    """

    ai_result = await call_qwen(prompt)

    answer_obj = Answer(
        session_id=session_id,
        answer=answer,
        score=5  # later parse AI
    )
    db.add(answer_obj)
    db.commit()

    return ai_result