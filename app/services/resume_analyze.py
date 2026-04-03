from app.llm.ats_score import calculate_ats_score


async def analyze_resume(resume_text: str, job_desc: str):
    return await calculate_ats_score(resume_text, job_desc)