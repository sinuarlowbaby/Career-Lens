from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.routes.api.routes import router
from app.routes.api.upload import router as upload_router
from app.routes.api.auth import router as auth_router
from app.routes.api.ai import router as ai_router
import dotenv
import os

dotenv.load_dotenv()

# ── Fail loudly on missing secrets ────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")

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

    # Step 2: Idempotent column migrations — safe to run on every startup.
    # These handle cases where a table already existed before a column was added.
    column_migrations = [
        # users table — add columns introduced after initial creation
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS picture VARCHAR(512);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();",
    ]
    with engine.connect() as conn:
        for sql in column_migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                logger.warning(f"Migration skipped ({sql.strip()}): {e}")

    logger.info("✅ Column migrations applied")
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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})
