from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from jose import jwt, JWTError
import datetime
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)


def create_access_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


@router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})


@router.get("/login/google")
async def google_login(request: Request):
    redirect_uri = str(request.url_for('google_callback'))
    logger.info(f"[OAuth] Starting Google login, redirect_uri={redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    # ── Step 1: Exchange code for token ───────────────────────────────────────
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"[OAuth] Token exchange failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OAuth token exchange failed: {str(e)}"
        )

    user_info = token.get("userinfo")
    if not user_info:
        logger.error("[OAuth] userinfo missing from token response")
        raise HTTPException(status_code=400, detail="Could not fetch user info from Google")

    logger.info(f"[OAuth] Google login for email={user_info.get('email')}")

    # ── Step 2: Upsert user in database ───────────────────────────────────────
    try:
        user = db.query(User).filter(User.email == user_info["email"]).first()
        if not user:
            user = User(
                email=user_info["email"],
                name=user_info.get("name", ""),
                google_id=user_info["sub"],
                picture=user_info.get("picture", ""),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[OAuth] Created new user id={user.id}")
        else:
            # Keep profile picture and name up to date
            updated = False
            if user_info.get("picture") and getattr(user, "picture", None) != user_info["picture"]:
                user.picture = user_info["picture"]
                updated = True
            if user_info.get("name") and user.name != user_info["name"]:
                user.name = user_info["name"]
                updated = True
            if updated:
                db.commit()
            logger.info(f"[OAuth] Found existing user id={user.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"[OAuth] DB upsert failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error during login: {str(e)}")

    # ── Step 3: Issue JWT and redirect ────────────────────────────────────────
    access_token = create_access_token(user.id, user.email)
    redirect_url = f"{FRONTEND_URL}/#access_token={access_token}"
    logger.info(f"[OAuth] Redirecting to {FRONTEND_URL}/ with token")
    return RedirectResponse(url=redirect_url)


@router.get("/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    """Returns the currently logged-in user profile. JWT from Authorization: Bearer <token>."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)

    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    resume = sorted(user.resumes, key=lambda x: x.created_at, reverse=True)[0] if user.resumes else None
    jd = sorted(user.job_descriptions, key=lambda x: x.created_at, reverse=True)[0] if user.job_descriptions else None

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "picture": getattr(user, "picture", "") or "",
        "resume": {
            "filename": resume.upload_filename,
            "text": resume.content
        } if resume else None,
        "job_description": {
            "text": jd.content
        } if jd else None,
    }


@router.post("/logout")
async def logout():
    # JWT is stateless — client deletes the token from localStorage.
    return {"message": "Logged out successfully."}