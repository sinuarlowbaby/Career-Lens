from fastapi import APIRouter

from app.routes.api import auth, upload, ai

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(upload.router, prefix="/upload", tags=["Upload"])
router.include_router(ai.router, prefix="/ai", tags=["AI"])