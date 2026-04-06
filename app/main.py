# ── Auto-Install Missing Dependencies ────────────────────────────────────────
import sys
import subprocess

def _ensure_deps():
    reqs = {
        "multipart": "python-multipart",
        "pdfplumber": "pdfplumber",
        "docx": "python-docx",
        "PyPDF2": "PyPDF2"
    }
    missing = []
    for mod, pkg in reqs.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"📦 Auto-installing missing packages: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("✅ Packages successfully installed!")

_ensure_deps()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env explicitly before importing any modules that rely on os.getenv()
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# ── Fail loudly on missing secrets BEFORE importing routes ────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "my_super_secret_development_key_123")

if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ WARNING: OPENAI_API_KEY is missing from .env! Using a dummy key so the server can start.")
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-to-bypass-error"

groq_key = os.getenv("GROQ_API_KEY_LLM") or os.getenv("GROQ_API_KEY") or ""
groq_key = groq_key.strip(' "\'')

os.environ["GROQ_API_KEY_LLM"] = groq_key
os.environ["GROQ_API_KEY"] = groq_key
if groq_key:
    print(f"✅ SUCCESS: Loaded real Groq key starting with: {groq_key[:8]}...")

# ── Auto-Start ChromaDB ───────────────────────────────────────────────────────
import socket
import subprocess
import time

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

if not is_port_in_use(8001):
    print("🚀 Starting ChromaDB Server automatically in the background...")
    subprocess.Popen(
        "chroma run --path ./chroma_data --port 8001",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)  # Wait for ChromaDB to be fully ready before importing routes

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.routes.api.routes import router
from app.routes.api.upload import router as upload_router
from app.routes.api.auth import router as auth_router
from app.routes.api.ai import router as ai_router
from app.routes.api.chroma_proxy import router as chroma_proxy_router

# ── CORS: list your actual origins (wildcard + credentials is rejected by browsers) ──
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:3000").split(",")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up CareerLens...")

    from app.db.database import engine, Base
    from app.db import models  # noqa: F401 — registers ALL models with Base
    from sqlalchemy import text

    # Step 1: Create any missing tables (new tables added to models.py appear here)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables verified/created")
    
    print("🚀 FastAPI server is ready!")
    print("APP UI  →  http://localhost:8000")
    print("📖 Swagger UI  →  http://localhost:8000/docs")
    yield
    logger.info("🛑 Shutting down CareerLens...")

app = FastAPI(title="Career Lens", description="Career Lens AI", version="1.0.0", lifespan=lifespan)

templates = Jinja2Templates(directory="app/templates")

# SessionMiddleware MUST be added before CORSMiddleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # No more wildcard — browsers require explicit origins with credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(upload_router)
app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(chroma_proxy_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Server Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server Error: {str(exc)}"}
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})


@app.get("/chroma-ui", response_class=HTMLResponse)
async def read_chroma_ui(request: Request):
    return templates.TemplateResponse(request=request, name="chromadb-ui_1.html", context={"request": request})