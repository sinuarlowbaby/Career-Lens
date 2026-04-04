from groq import AsyncGroq,APIError,RateLimitError
import os
from dotenv import load_dotenv

load_dotenv()
client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY"),
)

async def generate_response(prompt: str):
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
    except RateLimitError:
        return "Rate limit exceeded. Please try again later."
    except APIError as e:
        return f"API error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
    return response.choices[0].message.content