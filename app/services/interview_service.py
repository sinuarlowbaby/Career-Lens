from sqlalchemy.orm import Session
from app.db.models import InterviewSession, Answer
from app.llm.question_generator import generate_questions
from app.llm.answer_evaluation import evaluate_answer


def create_session(db: Session, user_id: int, role: str):
    session = InterviewSession(user_id=user_id, role=role)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


async def get_questions(role: str):
    return await generate_questions(role)


async def evaluate_user_answer(db: Session, session_id: int, answer: str):
    ai_result = await evaluate_answer(answer)

    answer_obj = Answer(session_id=session_id, answer=answer, score=5)
    db.add(answer_obj)
    db.commit()

    return ai_result