import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Local LLM configuration
LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen:3.5-2b")

async def generate_response(prompt: str):
    """Generate response using local Qwen model"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{LOCAL_LLM_BASE_URL}/chat/completions",
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]