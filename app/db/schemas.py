from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True


class ResumeOut(BaseModel):
    id: int
    content: str

    class Config:
        from_attributes = True