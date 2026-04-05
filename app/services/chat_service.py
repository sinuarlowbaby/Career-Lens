import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


async def generate_ai_response(prompt: str, system: str = "You are an AI career coach", history: list = None):
    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY_LLM", "").strip(' "\''),
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