from fastapi import APIRouter

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/resume")
async def upload_resume():
    return {"message": "Hello World"}

@router.post("/job_description")
async def upload_job_description():
    return {"message": "Hello World"}