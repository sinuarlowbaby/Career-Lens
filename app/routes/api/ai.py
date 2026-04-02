from fastapi import APIRouter
from app.llm.llm_client import generate_response

router = APIRouter()

@router.post("/ask")
async def ask_ai(prompt: str):
    result = await generate_response(prompt)
    return result