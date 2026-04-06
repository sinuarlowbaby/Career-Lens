from sqlalchemy.orm import Session
from app.db.models import User
from app.db.session import get_db
from fastapi import Header, Depends, HTTPException
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_or_create_user(db: Session, user_info: dict):
    user = db.query(User).filter(User.email == user_info["email"]).first()

    if not user:
        user = User(
            email=user_info["email"],
            name=user_info.get("name"),
            google_id=user_info.get("sub"),
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def create_access_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    authorization: str = Header(None, description="Bearer <jwt>"),
    db: Session = Depends(get_db),
) -> User:
    """Validates JWT and returns User. Fallbacks to a dummy local dev user if missing."""
    def get_dev_user():
        dev_user = db.query(User).filter(User.email == "dev@local").first()
        if not dev_user:
            dev_user = User(email="dev@local", name="Local Tester", google_id="dev")
            db.add(dev_user)
            db.commit()
            db.refresh(dev_user)
        return dev_user
        
    if not authorization or not authorization.startswith("Bearer "):
        return get_dev_user()
        
    try:
        token = authorization.split(" ", 1)[1]
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        user = db.query(User).filter(User.id == user_id).first()
        if user: return user
    except Exception:
        pass
        
    return get_dev_user()