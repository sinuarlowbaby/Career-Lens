from app.llm.gap_analyzer import analyze_gap


async def analyze_skill_gap(resume_text: str, job_desc: str):
    return await analyze_gap(resume_text, job_desc)