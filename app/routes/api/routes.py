from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.post("/chat")
async def chat():
    return {"message": "Hello World"}

@router.post("/ats")
async def ats():
    return {"message": "Hello World"}

@router.post("/interview")
async def interview():
    return {"message": "Hello World"}

@router.post("/skill_gap")
async def skill_gap():
    return {"message": "Hello World"}

@router.post("/auth")
async def auth():
    return {"message": "Hello World"}


