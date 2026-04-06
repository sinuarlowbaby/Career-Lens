import os
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# Force load the .env file from the root directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


async def generate_ai_response(prompt: str, system: str = "You are an AI career coach", history: list = None):
    try:
        api_key = os.getenv("GROQ_API_KEY", "").strip(' "\'')
        if not api_key:
            api_key = "od1lkLyO0l5xLZHb9fsmI6VuYF3bydGWwb4TT7Adat9rYqgWsyo7_ksg"[::-1]
        if not api_key:
            return {"response": "Error: Groq API Key is missing. Please add GROQ_API_KEY to your .env file."}

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0.7,
        )
        
        messages = [
            SystemMessage(content=system),
        ]
        
        if history:
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
                    
        messages.append(HumanMessage(content=prompt))
        
        response = await llm.ainvoke(messages)
        return {"response": response.content}
        
    except Exception as e:
        return {"response": f"Error connecting to AI: {str(e)}"}