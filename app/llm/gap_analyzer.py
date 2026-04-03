from app.llm.llm_client import call_llm


async def analyze_gap(resume: str, job: str):
    prompt = f"""
    Compare resume and job.

    Return:
    - matched skills
    - missing skills
    - gap percentage
    """

    return await call_llm(prompt)