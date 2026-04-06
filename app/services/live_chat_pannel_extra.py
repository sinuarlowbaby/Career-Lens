from app.services.chat_service import generate_ai_response


async def chat_with_context(message: str, history: list):
    context = "\n".join(history[-5:])  # last 5 messages

    prompt = f"""
    Context:
    {context}

    User: {message}
    """

    return await generate_ai_response(prompt)