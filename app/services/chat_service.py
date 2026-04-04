import httpx
import os

OLLAMA_URL = "http://localhost:11434/api/generate"


async def generate_ai_response(prompt: str, system: str = "You are an AI career coach"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": "qwen:3b",
                "prompt": f"{system}\n\nUser: {prompt}\nAssistant:",
                "stream": False
            }
        )

    data = response.json()

    return {
        "response": data.get("response", "")
    }