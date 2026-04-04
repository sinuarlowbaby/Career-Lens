from fastapi import APIRouter, HTTPException
from app.llm.llm_client import generate_response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["ai"])


class Prompt(BaseModel):
    prompt: str = Field(..., description="Prompt to send to the AI", min_length=1, max_length=4000)


class AskResponse(BaseModel):
    response: str


@router.post("/ask", response_model=AskResponse)
async def ask_ai(body: Prompt):
    # Bug fix: was passing the whole Pydantic object — must pass body.prompt (the string)
    result = await generate_response(body.prompt)
    return AskResponse(response=result)
