from app.llm.llm_client import call_llm_async
from app.rag.query_pipeline import query_knowledge_base


async def chat_with_ai(message: str):
    context = query_knowledge_base(message)

    prompt = f"""
    Context:
    {context}

    User:
    {message}
    """

    return await call_llm_async(prompt)