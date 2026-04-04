from app.services.chat_service import generate_ai_response


async def analyze_resume_with_ai(resume_text: str, job_desc: str):
    prompt = f"""
    Analyze this resume against job description.

    Resume:
    {resume_text}

    Job:
    {job_desc}

    Return:
    - ATS score (0-100)
    - Missing skills
    - Suggestions
    """

    result = await generate_ai_response(prompt)

    return result