from fastapi import APIRouter
from app.llm.llm_client import generate_response
from pydantic import BaseModel,Field

router = APIRouter(prefix="/ai", tags=["ai"])

class Prompt(BaseModel):
    prompt: str = Field(..., description="Prompt to be sent to the AI",min_length=1,max_length=1000)

@router.post("/ask")
async def ask_ai(prompt: Prompt):
    result = await generate_response(prompt)
    return result