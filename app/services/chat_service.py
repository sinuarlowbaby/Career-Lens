from app.llm.llm_client import generate_response
import asyncio


async def call_qwen(prompt: str, system: str = "You are an AI career coach"):
    """Call Groq LLM for AI responses"""
    full_prompt = f"{system}\n\n{prompt}"
    return await generate_response(full_prompt)


async def generate_ai_response(prompt: str, context: dict = None):
    response = await call_qwen(prompt)

    return {
        "response": response,
        "context": context
    }