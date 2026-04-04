from app.services.chat_service import generate_ai_response


async def analyze_gap_ai(resume_text: str, job_desc: str):
    prompt = f"""
    Compare resume and job description.

    Return:
    - matched skills
    - missing skills
    - gap percentage
    """

    return await generate_ai_response(prompt)