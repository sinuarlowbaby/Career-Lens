from app.llm.llm_client import call_llm


async def evaluate_answer(answer: str):
    prompt = f"""
    Evaluate this answer:

    {answer}

    Return:
    - score (0-10)
    - feedback
    - improvements
    """

    return await call_llm(prompt)