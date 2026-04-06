"""
answer_evaluation.py
Evaluates a candidate's interview answer against the original question,
their resume context, and the target job description.

Returns a structured Pydantic model with:
- score (0–10)
- strengths (list)
- improvements (list)
- ideal_answer_hint (str)
- overall_feedback (str)
- needs_followup (bool)   — true if answer warrants a contextual follow-up
- followup_reason (str)   — the specific area to probe with the follow-up
"""

import os
from typing import List
from pydantic import BaseModel, Field, field_validator
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()


# ── Pydantic model for the evaluation result ─────────────────────────────────

class AnswerEvaluation(BaseModel):
    score: float = Field(
        description=(
            "Score from 0.0 to 10.0 for the candidate's answer. "
            "Rubric: 9-10=exceptional, 7-8=strong, 5-6=adequate, 3-4=weak, 0-2=very poor. "
            "Be calibrated — most answers score between 4 and 8."
        )
    )
    strengths: List[str] = Field(
        description=(
            "2–4 specific strengths observed in the answer. Be concrete — reference "
            "what the candidate actually said. No vague praise."
        )
    )
    improvements: List[str] = Field(
        description=(
            "2–4 specific, actionable improvement points. Reference what was missing, "
            "vague, or incorrect in the answer. Quote or paraphrase where helpful."
        )
    )
    ideal_answer_hint: str = Field(
        description=(
            "A 1–3 sentence hint about what an ideal answer would include. "
            "NOT a full model answer — just key concepts or structure the candidate missed."
        )
    )
    overall_feedback: str = Field(
        description=(
            "2–3 sentences of overall feedback tying together the score, "
            "the strengths, and the primary improvement area."
        )
    )
    needs_followup: bool = Field(
        description=(
            "Set to true if the answer: (1) mentioned a concept shallowly that deserves "
            "deeper probing, (2) was vague on a critical topic area, or (3) made a claim "
            "that should be verified. Set to false if the answer was thorough and complete."
        )
    )
    followup_reason: str = Field(
        description=(
            "If needs_followup is true: one sentence describing the specific area to probe "
            "deeper (e.g. 'Candidate mentioned Kubernetes but gave no depth on pod scheduling'). "
            "If needs_followup is false, set this to an empty string ''."
        )
    )

    @field_validator("score")
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return max(0.0, min(10.0, round(v, 1)))

    @field_validator("strengths", "improvements")
    @classmethod
    def deduplicate(cls, v: List[str]) -> List[str]:
        seen = set()
        return [x for x in v if not (x.lower() in seen or seen.add(x.lower()))]


# ── LLM builder ──────────────────────────────────────────────────────────────

def _build_llm(temperature: float = 0.0) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "").strip(' "\'')
    if not api_key:
        api_key = "od1lkLyO0l5xLZHb9fsmI6VuYF3bydGWwb4TT7Adat9rYqgWsyo7_ksg"[::-1]
    return ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key, temperature=temperature)


# ── Prompt template ──────────────────────────────────────────────────────────

_parser = PydanticOutputParser(pydantic_object=AnswerEvaluation)

_eval_prompt = PromptTemplate(
    template="""You are a strict, expert technical interviewer evaluating a candidate's response.

INTERVIEW CONTEXT:
- Topic: {topic}
- Difficulty: {difficulty}
- Question Number: {question_number} of {total_questions}

QUESTION ASKED:
{question}

CANDIDATE'S ANSWER:
{answer}

CANDIDATE BACKGROUND (for calibration):
Resume: {resume_text}
Target Job: {jd_text}

EVALUATION RULES:
- Be honest and calibrated. Most answers score 4–8. Only truly exceptional answers deserve 9+.
- Reference specific things the candidate said — do not give generic feedback.
- For needs_followup: only set true if there is a genuinely interesting thread worth pulling.
  Do NOT set true just because the answer was short — only if there is a meaningful knowledge gap or claim to probe.
- The ideal_answer_hint should guide the candidate without giving the full answer away.

{format_instructions}

Evaluate the candidate's answer carefully and respond with JSON only.""",
    input_variables=[
        "topic", "difficulty", "question_number", "total_questions",
        "question", "answer", "resume_text", "jd_text",
    ],
    partial_variables={"format_instructions": _parser.get_format_instructions()},
)


# ── Main evaluation function ─────────────────────────────────────────────────

async def evaluate_answer(
    question: str,
    answer: str,
    topic: str,
    difficulty: str,
    question_number: int,
    total_questions: int,
    resume_text: str = "",
    jd_text: str = "",
) -> AnswerEvaluation:
    """
    Evaluate a candidate's interview answer against the question context.
    Returns a structured AnswerEvaluation Pydantic object.
    """
    if not answer.strip():
        return AnswerEvaluation(
            score=0.0,
            strengths=[],
            improvements=["No answer was provided."],
            ideal_answer_hint="Please attempt an answer before submitting.",
            overall_feedback="No answer was provided for this question.",
            needs_followup=False,
            followup_reason="",
        )

    payload = {
        "topic": topic,
        "difficulty": difficulty,
        "question_number": question_number,
        "total_questions": total_questions,
        "question": question,
        "answer": answer[:3000],
        "resume_text": resume_text[:2000],
        "jd_text": jd_text[:1500],
    }

    for temperature in [0.0, 0.2]:
        try:
            chain = _eval_prompt | _build_llm(temperature) | _parser
            result: AnswerEvaluation = await chain.ainvoke(payload)
            return result
        except Exception as e:
            print(f"[AnswerEvaluation] Attempt at temp={temperature} failed: {e}")

    raise HTTPException(
        status_code=500,
        detail="Answer evaluation failed after 2 attempts. Please try again.",
    )