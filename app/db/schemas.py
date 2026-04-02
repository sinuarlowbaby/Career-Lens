from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    name: str
    google_id: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        orm_mode = True