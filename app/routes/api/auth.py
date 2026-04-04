from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from jose import jwt
import datetime
import os

router = APIRouter(prefix="/auth", tags=["auth"])

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


@router.get("/login/google")
async def google_login(request: Request):
    # NOTE: The callback name must match the function name below exactly
    redirect_uri = str(request.url_for('google_callback'))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(status_code=400, detail="Could not fetch user info from Google")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"OAuth login failed: {str(e)}")

    # Upsert user
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
            email=user_info["email"],
            name=user_info["name"],
            google_id=user_info["sub"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user.id, user.email)

    # Redirect back to your frontend with the token in the URL hash
    # Your frontend JS can read it with: new URLSearchParams(window.location.hash.slice(1))
    return RedirectResponse(
        url=f"{FRONTEND_URL}/#access_token={access_token}"
    )


@router.post("/logout")
async def logout():
    # JWT is stateless — logout is handled client-side by deleting the token.
    # If you need server-side revocation later, add a token denylist in Redis.
    return {"message": "Logged out. Please delete the token on the client."}
