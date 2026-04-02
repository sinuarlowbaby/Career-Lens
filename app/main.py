from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.routes.api.routes import router
from app.routes.api.upload import router as upload_router
from app.routes.api.auth import router as auth_router
from app.routes.api.ai import router as ai_router
import dotenv
import os

dotenv.load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG pipeline...")
    print("Starting up...")
    print("🚀 FastAPI server is ready!")
    print("APP UI  →  http://localhost:8000")
    print("📖 Swagger UI  →  http://localhost:8000/docs")
    yield
    print("Shutting down...")
    logger.info("🛑 shutting down System...")

app = FastAPI(title="Career Lens", description="Career Lens", version="1.0.0", lifespan=lifespan)
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(upload_router)
app.include_router(auth_router)
app.include_router(ai_router)



@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})
