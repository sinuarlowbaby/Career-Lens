from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login():
    return {"message": "Hello World"}

@router.post("/register")
async def register():
    return {"message": "Hello World"}

@router.post("/logout")
async def logout():
    return {"message": "Hello World"}

@router.post("/forgot_password")
async def forgot_password():
    return {"message": "Hello World"}

@router.post("/reset_password")
async def reset_password():
    return {"message": "Hello World"}

@router.post("/change_password")
async def change_password():
    return {"message": "Hello World"}
