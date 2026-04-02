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

from fastapi import Depends
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
import os


oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

@router.get("/login/google")
async def google_login(request: Request):
    redirect_uri = str(request.url_for('google_callback'))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token["userinfo"]

    # Check if user exists
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

    return {"message": "Login successful", "user": user.email}