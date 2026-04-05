from groq import AsyncGroq, APIError, RateLimitError
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))


async def generate_response(prompt: str, system_prompt: str = None) -> str:
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content

    except RateLimitError:
        # Bug fix: returning a string silently swallowed errors — raise proper HTTP errors instead
        raise HTTPException(status_code=429, detail="LLM rate limit reached. Please try again later.")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"LLM API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")