import httpx
import asyncio

OLLAMA_URL = "http://localhost:11434/api/generate"


async def call_qwen(prompt: str, system: str = "You are an AI career coach"):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": "qwen:3b",
                "prompt": f"{system}\n\n{prompt}",
                "stream": False
            }
        )

    return response.json().get("response", "")


async def generate_ai_response(prompt: str, context: dict = None):
    response = await call_qwen(prompt)

    return {
        "response": response,
        "context": context
    }