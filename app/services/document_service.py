import os
from sqlalchemy.orm import Session
from app.db.models import User

UPLOAD_DIR = "uploads"


def save_file(file):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def extract_text(file_path: str):
    # Replace later with pdfplumber / PyMuPDF
    return "parsed resume text from file"


def store_resume(db: Session, user_id: int, text: str):
    resume = Resume(
        user_id=user_id,
        content=text
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


def process_resume(db: Session, user_id: int, file):
    path = save_file(file)
    text = extract_text(path)
    resume = store_resume(db, user_id, text)

    return {
        "resume_id": resume.id,
        "text": text
    }