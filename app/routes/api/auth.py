from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from jose import jwt
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
                google_id=user_info["sub"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[OAuth] Created new user id={user.id}")
        else:
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


@router.post("/logout")
async def logout():
    # JWT is stateless — logout is handled client-side by deleting the token.
    # If you need server-side revocation later, add a token denylist in Redis.
    return {"message": "Logged out. Please delete the token on the client."}
