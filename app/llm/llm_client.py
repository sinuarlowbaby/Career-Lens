import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def call_llm(prompt: str, system: str = "You are an AI career coach"):
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # fast + powerful
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"LLM Error: {str(e)}"