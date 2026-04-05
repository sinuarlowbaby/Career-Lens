import json
import re
from app.llm.llm_client import call_llm_async


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else "{}"


async def analyze_resume(resume_text: str, job_desc: str):
    prompt = f"""
    Analyze resume vs job description.

    Return JSON ONLY:
    {{
        "score": 0-100,
        "matched_skills": [],
        "missing_skills": [],
        "suggestions": []
    }}

    Resume:
    {resume_text}

    Job:
    {job_desc}
    """

    raw = await call_llm_async(prompt)

    try:
        return json.loads(extract_json(raw))
    except:
        return {
            "score": 50,
            "matched_skills": [],
            "missing_skills": [],
            "suggestions": [raw]
        }