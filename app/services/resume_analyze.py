import json
import re
from app.llm.llm_client import generate_response


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

    raw = await generate_response(prompt)

    try:
        return json.loads(extract_json(raw))
    except Exception as e:
        return {
            "score": 50,
            "matched_skills": [],
            "missing_skills": [],
            "suggestions": [f"AI Parsing Error: {str(e)}", raw]
        }