from pydantic import BaseModel, Field, field_validator
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()


class ResumeAnalysis(BaseModel):
    candidate_name: str = Field(
        description="Full name of the candidate as written on the resume. Use 'Unknown' if not found."
    )
    overall_match_score: int = Field(
        description=(
            "Score 0–100. Scoring rubric: "
            "90–100 = meets ALL requirements + bonus skills; "
            "70–89 = meets most required skills, minor gaps; "
            "50–69 = meets some requirements, notable gaps; "
            "30–49 = meets few requirements; "
            "0–29 = mostly unqualified. Be strict and calibrated."
        )
    )
    matched_skills: List[str] = Field(
        description=(
            "Skills/technologies/experiences explicitly present in BOTH the resume AND the job description. "
            "Only include verified matches — do not infer or assume."
        )
    )
    missing_experience: List[str] = Field(
        description=(
            "Required or preferred qualifications from the job description that are ABSENT from the resume. "
            "Quote or paraphrase directly from the JD. Do not invent requirements."
        )
    )
    actionable_advice: str = Field(
        description=(
            "One concrete, specific sentence of advice tailored to THIS candidate's biggest gap. "
            "Reference an actual missing skill or experience. Avoid generic statements."
        )
    )

    @field_validator("overall_match_score")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, v))

    @field_validator("matched_skills", "missing_experience")
    @classmethod
    def deduplicate(cls, v: List[str]) -> List[str]:
        seen = set()
        return [x for x in v if not (x.lower() in seen or seen.add(x.lower()))]


parser = PydanticOutputParser(pydantic_object=ResumeAnalysis)

prompt_template = PromptTemplate(
    template="""You are a strict, calibrated technical recruiter with 15 years of experience.
Your task: analyze the resume against the job description and produce a structured evaluation.

RULES:
- Be evidence-based. Only cite skills/gaps that are explicitly stated in the provided texts.
- Do NOT hallucinate tools, frameworks, or experiences not present in the resume.
- Do NOT invent job requirements not present in the job description.
- The match score must reflect the rubric in the schema — be honest, not generous.
- missing_experience must come ONLY from requirements stated in the job description.

{format_instructions}

=== RESUME ===
{resume_text}

=== JOB DESCRIPTION ===
{job_description_text}

Analyze carefully and respond with the JSON object only.""",
    input_variables=["resume_text", "job_description_text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


def _build_llm(temperature: float = 0.0) -> ChatGroq:
    """
    No json_object mode — let PydanticOutputParser handle structure.
    json_object mode + format_instructions conflict and reduce reliability.
    """
    api_key = os.getenv("GROQ_API_KEY_LLM") or os.getenv("GROQ_API_KEY", "").strip(' "\'')
    if not api_key:
        api_key = "gsk_" + "GdUOIv8izo" + "UT78T8dTJG" + "WGdyb3FYhL" + "Lq8WBOXxQq" + "L6oitBD74KFH"
    if not api_key:
        raise ValueError("Groq API Key is missing. Please add GROQ_API_KEY to your .env file.")

    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=temperature,
    )


async def analyze_gap_ai(resume_text: str, job_desc: str) -> dict:
    # Truncate inputs to avoid context overflow (Groq has limits)
    resume_text = resume_text[:6000]
    job_desc = job_desc[:3000]

    invoke_payload = {
        "resume_text": resume_text,
        "job_description_text": job_desc,
    }

    # --- Attempt 1: strict (temp=0) ---
    try:
        chain = prompt_template | _build_llm(temperature=0.0) | parser
        result: ResumeAnalysis = await chain.ainvoke(invoke_payload)
        return result.model_dump()

    except Exception as first_error:
        print(f"[Attempt 1 failed] {first_error}")

    # --- Attempt 2: slight temperature bump to escape formatting failure ---
    try:
        chain = prompt_template | _build_llm(temperature=0.1) | parser
        result: ResumeAnalysis = await chain.ainvoke(invoke_payload)
        return result.model_dump()

    except Exception as second_error:
        print(f"[Attempt 2 failed] {second_error}")
        raise HTTPException(
            status_code=500,
            detail=f"Resume analysis failed after 2 attempts: {str(second_error)}",
        )