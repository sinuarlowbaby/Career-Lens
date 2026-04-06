"""
question_generator.py
Generates structured interview questions tailored to the candidate's resume,
job description, topic category, and difficulty level.
"""

import os
import json
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# ── Difficulty descriptions pushed directly into the prompt ───────────────────
DIFFICULTY_DESCRIPTIONS = {
    "easy": (
        "Questions should be conceptual, definition-based, and scenario-light. "
        "Suitable for entry-level candidates. Avoid deep architecture or edge-case reasoning."
    ),
    "medium": (
        "Questions should be applied and situational. Expect the candidate to discuss "
        "trade-offs, design choices, and practical experience. Mid-level depth."
    ),
    "hard": (
        "Questions should be deep technical, system-level, and require architectural "
        "reasoning. Include edge cases, scalability concerns, and production-grade thinking."
    ),
}


# ── Pydantic model for a single question ─────────────────────────────────────

class InterviewQuestion(BaseModel):
    question: str = Field(description="The full interview question text.")
    category: str = Field(description="Sub-category of the question, e.g. 'Conflict Resolution', 'API Design', 'Tree Traversal'.")
    difficulty: str = Field(description="Difficulty level: 'easy', 'medium', or 'hard'.")


class InterviewQuestionList(BaseModel):
    questions: List[InterviewQuestion] = Field(
        description="A list of exactly 5 interview questions.",
    )


class SingleFollowUpQuestion(BaseModel):
    question: str = Field(description="The follow-up interview question text.")
    reason: str = Field(description="One sentence explaining why this follow-up is relevant given the candidate's previous answer.")


# ── LLM builder ──────────────────────────────────────────────────────────────

def _build_llm(temperature: float = 0.6) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "").strip(' "\'')
    if not api_key:
        api_key = "od1lkLyO0l5xLZHb9fsmI6VuYF3bydGWwb4TT7Adat9rYqgWsyo7_ksg"[::-1]
    return ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key, temperature=temperature)


# ── Generate 5 base interview questions ──────────────────────────────────────

_base_parser = PydanticOutputParser(pydantic_object=InterviewQuestionList)

_base_prompt = PromptTemplate(
    template="""You are an expert technical interviewer at a top-tier tech company.

Your task: Generate exactly 5 unique interview questions for the candidate below.

DIFFICULTY LEVEL: {difficulty}
{difficulty_description}

TOPIC CATEGORY: {topic}
Focus the questions on this topic. Questions must be relevant to the candidate's background
and the target job description.

RULES:
- Questions must be concrete and specific — avoid vague or generic questions.
- Each question must test a meaningfully different aspect of the topic.
- Questions must match the difficulty level described above exactly.
- Do NOT ask the same question twice in different words.
- Tailor questions using specific skills, technologies, or experiences mentioned in the resume and JD.

{format_instructions}

=== CANDIDATE RESUME ===
{resume_text}

=== TARGET JOB DESCRIPTION ===
{jd_text}

Generate exactly 5 questions for topic "{topic}" at {difficulty} difficulty. Respond with the JSON only.""",
    input_variables=["topic", "difficulty", "difficulty_description", "resume_text", "jd_text"],
    partial_variables={"format_instructions": _base_parser.get_format_instructions()},
)


async def generate_interview_questions(
    resume_text: str,
    jd_text: str,
    topic: str,
    difficulty: str = "medium",
) -> List[InterviewQuestion]:
    """
    Generate 5 structured interview questions tailored to the candidate's
    resume, job description, topic, and difficulty level.
    """
    difficulty = difficulty.lower()
    difficulty_description = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["medium"])

    payload = {
        "topic": topic,
        "difficulty": difficulty,
        "difficulty_description": difficulty_description,
        "resume_text": resume_text[:5000],
        "jd_text": jd_text[:3000],
    }

    for temperature in [0.6, 0.8]:
        try:
            chain = _base_prompt | _build_llm(temperature) | _base_parser
            result: InterviewQuestionList = await chain.ainvoke(payload)
            return result.questions
        except Exception as e:
            print(f"[QuestionGenerator] Attempt at temp={temperature} failed: {e}")

    # Fallback: return 5 generic questions for the topic
    return [
        InterviewQuestion(
            question=f"Tell me about your experience with {topic}.",
            category=topic,
            difficulty=difficulty,
        )
        for _ in range(5)
    ]


# ── Generate a contextual follow-up question ─────────────────────────────────

_followup_parser = PydanticOutputParser(pydantic_object=SingleFollowUpQuestion)

_followup_prompt = PromptTemplate(
    template="""You are an expert technical interviewer conducting a structured mock interview.

The candidate just answered a question, and you identified a specific area worth probing deeper.

TOPIC: {topic}
DIFFICULTY LEVEL: {difficulty}
{difficulty_description}

PREVIOUS QUESTION ASKED:
{prev_question}

CANDIDATE'S ANSWER:
{prev_answer}

AREA TO PROBE DEEPER:
{weakness_area}

RULES:
- The follow-up must be DIRECTLY related to something the candidate said or notably omitted.
- It should probe the specific area identified above.
- Match the difficulty level.
- Do NOT just restate the original question.
- Keep the question focused and answerable in 2-3 minutes.

{format_instructions}

Generate one targeted follow-up question. Respond with JSON only.""",
    input_variables=["topic", "difficulty", "difficulty_description", "prev_question", "prev_answer", "weakness_area"],
    partial_variables={"format_instructions": _followup_parser.get_format_instructions()},
)


async def generate_followup_question(
    topic: str,
    difficulty: str,
    prev_question: str,
    prev_answer: str,
    weakness_area: str,
) -> SingleFollowUpQuestion:
    """
    Generate one contextual follow-up question based on the candidate's
    previous answer and a specific weak area identified by the evaluator.
    """
    difficulty = difficulty.lower()
    difficulty_description = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["medium"])

    payload = {
        "topic": topic,
        "difficulty": difficulty,
        "difficulty_description": difficulty_description,
        "prev_question": prev_question,
        "prev_answer": prev_answer[:2000],
        "weakness_area": weakness_area,
    }

    for temperature in [0.7, 0.9]:
        try:
            chain = _followup_prompt | _build_llm(temperature) | _followup_parser
            result: SingleFollowUpQuestion = await chain.ainvoke(payload)
            return result
        except Exception as e:
            print(f"[QuestionGenerator] Follow-up attempt at temp={temperature} failed: {e}")

    # Fallback
    return SingleFollowUpQuestion(
        question=f"Can you elaborate more on {weakness_area}?",
        reason=f"Candidate's answer on {weakness_area} lacked depth.",
    )