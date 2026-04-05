"""
upload.py  —  /upload/resume  &  /upload/job_description
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Resume, JobDescription
from app.services.document_service import process_resume, process_job_description_text
from app.services.auth_service import get_current_user
from app.rag.ingestion_pipeline import ingestion_pipeline
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


# ── Request schemas ────────────────────────────────────────────────────────────

class JobDescriptionRequest(BaseModel):
    content: str
    title: str | None = None


# ── POST /upload/resume ────────────────────────────────────────────────────────

@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(..., description="PDF, DOCX or TXT resume file"),
    db:   Session    = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a resume file.
    - Saves the file to disk
    - Extracts plain text (pdfplumber / python-docx)
    - Stores the Resume row in the database
    - Returns the resume_id + extracted text
    """
    logger.info(f"[Upload] user_id={current_user.id} resume uploading {file.filename!r}")

    try:
        resume, text = process_resume(
            db      = db,
            user_id = current_user.id,
            file    = file,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"[Upload] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # ── Auto-embed: trigger if JD already exists ─────────────────────────────
    embedded = False
    jd = db.query(JobDescription).filter(JobDescription.user_id == current_user.id).order_by(JobDescription.created_at.desc()).first()
    if jd:
        try:
            await ingestion_pipeline(
                db=db,
                user_id=current_user.id,
                resume_content=text,
                job_description_content=jd.content,
                resume_id=resume.id,
                jd_id=jd.id,
            )
            embedded = True
            logger.info(f"[Upload] Auto-embedding complete for user_id={current_user.id}")
        except Exception as e:
            logger.error(f"[Upload] Auto-embedding failed: {e}", exc_info=True)

    return {
        "resume_id":  resume.id,
        "filename":   resume.upload_filename,
        "file_type":  resume.file_type,
        "text":       text,
        "char_count": len(text),
        "embedded":   embedded,
    }


# ── POST /upload/job_description ──────────────────────────────────────────────

@router.post("/job_description")
async def upload_job_description(
    body: JobDescriptionRequest,
    db:   Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Save a job description (pasted text from the frontend).
    - Stores the JD text in the job_descriptions table
    - Returns the jd_id + content preview
    """
    logger.info(f"[Upload] user_id={current_user.id} job_description text ({len(body.content)} chars)")

    try:
        jd = process_job_description_text(
            db      = db,
            user_id = current_user.id,
            content = body.content,
            title   = body.title,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Upload] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # ── Auto-embed: trigger if Resume already exists ───────────────────────────
    embedded = False
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    if resume:
        try:
            await ingestion_pipeline(
                db=db,
                user_id=current_user.id,
                resume_content=resume.content,
                job_description_content=jd.content,
                resume_id=resume.id,
                jd_id=jd.id,
            )
            embedded = True
            logger.info(f"[Upload] Auto-embedding complete for user_id={current_user.id}")
        except Exception as e:
            logger.error(f"[Upload] Auto-embedding failed: {e}", exc_info=True)

    return {
        "jd_id":      jd.id,
        "title":      jd.title,
        "char_count": len(jd.content),
        "embedded":   embedded,
    }