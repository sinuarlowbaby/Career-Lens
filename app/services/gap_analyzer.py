from app.services.chat_service import call_qwen


async def analyze_gap(resume_text: str, job_description: str):
    prompt = f"""
    Compare resume with job description.

    Return:
    - matched skills
    - missing skills
    - gap percentage
    """

    return await call_qwen(prompt)