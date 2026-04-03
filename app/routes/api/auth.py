from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import get_or_create_user, create_token

router = APIRouter()


@router.post("/login")
def login(user_info: dict, db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_info)
    token = create_token(user.id)

    return {"token": token, "user_id": user.id}