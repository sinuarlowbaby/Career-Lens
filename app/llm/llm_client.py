from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv()
client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY"),
)

async def generate_response(prompt: str):
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content