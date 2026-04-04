"""
document_service.py
───────────────────
Handles file saving, text extraction (PDF / DOCX / TXT),
and persisting the resume record to the database.

Returns: plain extracted text (str) so the caller can pass it
         straight into the RAG ingestion pipeline.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path

from sqlalchemy.orm import Session
from app.db.models import Resume, FileType

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")


# ── 1. File helpers ────────────────────────────────────────────────────────────

def save_file(file) -> tuple[Path, FileType]:
    """
    Writes an UploadFile to disk under UPLOAD_DIR.
    Returns (absolute_path, FileType enum).
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename: str = file.filename
    ext = Path(filename).suffix.lower().lstrip(".")

    # Validate extension
    ext_map = {"pdf": FileType.pdf, "docx": FileType.docx, "txt": FileType.txt}
    if ext not in ext_map:
        raise ValueError(f"Unsupported file type: .{ext}. Allowed: pdf, docx, txt")

    dest = UPLOAD_DIR / filename
    file.file.seek(0)
    dest.write_bytes(file.file.read())

    logger.info(f"[DocumentService] Saved file → {dest}")
    return dest, ext_map[ext]


# ── 2. Text extraction ─────────────────────────────────────────────────────────

def extract_text(file_path: Path, file_type: FileType) -> str:
    """
    Extracts plain text from a saved resume file.
    Requires: pdfplumber (PDF), python-docx (DOCX).
    """
    if file_type == FileType.pdf:
        return _extract_pdf(file_path)
    elif file_type == FileType.docx:
        return _extract_docx(file_path)
    else:  # txt
        return file_path.read_text(encoding="utf-8", errors="ignore")


def _extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        logger.warning("[DocumentService] pdfplumber not installed — falling back to PyPDF2")
        return _extract_pdf_fallback(path)


def _extract_pdf_fallback(path: Path) -> str:
    try:
        import PyPDF2
        text_parts = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)
    except ImportError:
        raise RuntimeError(
            "No PDF library found. Install pdfplumber: pip install pdfplumber"
        )


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise RuntimeError(
            "python-docx not installed. Run: pip install python-docx"
        )


# ── 3. Database persistence ────────────────────────────────────────────────────

def store_resume(
    db: Session,
    user_id: int,
    filename: str,
    file_path: Path,
    file_type: FileType,
    text_content: str,
) -> Resume:
    """
    Inserts (or replaces) the Resume row for this user + filename.
    If a resume with the same filename already exists for the user,
    its content is updated in-place (idempotent re-upload).
    """
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == user_id, Resume.upload_filename == filename)
        .first()
    )

    if resume:
        resume.text_content = text_content
        resume.file_path    = str(file_path)
        resume.file_type    = file_type
        logger.info(f"[DocumentService] Updated existing resume id={resume.id}")
    else:
        resume = Resume(
            user_id         = user_id,
            upload_filename = filename,
            file_path       = str(file_path),
            file_type       = file_type,
            text_content    = text_content,
        )
        db.add(resume)
        logger.info("[DocumentService] Creating new resume row")

    db.commit()
    db.refresh(resume)
    logger.info(f"[DocumentService] Resume id={resume.id} stored for user_id={user_id}")
    return resume


# ── 4. Orchestrator ────────────────────────────────────────────────────────────

def process_resume(db: Session, user_id: int, file) -> tuple[Resume, str]:
    """
    Full pipeline:
      save → extract text → store in DB
    Returns: (Resume ORM object, extracted_text)
    """
    # Step 1 — save to disk
    file_path, file_type = save_file(file)

    # Step 2 — extract text
    text = extract_text(file_path, file_type)
    if not text.strip():
        raise ValueError("No text could be extracted from the uploaded file.")

    # Step 3 — persist to DB
    resume = store_resume(
        db          = db,
        user_id     = user_id,
        filename    = file.filename,
        file_path   = file_path,
        file_type   = file_type,
        text_content= text,
    )

    return resume, text