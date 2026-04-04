from sqlalchemy import (
    Column, Integer, String, Text, Float, JSON,
    ForeignKey, DateTime, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class InterviewStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed   = "completed"
    abandoned   = "abandoned"

class FileType(str, enum.Enum):
    pdf  = "pdf"
    docx = "docx"
    txt  = "txt"


# ── A. Users ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=True)
    email      = Column(String(255), unique=True, index=True, nullable=False)
    google_id  = Column(String(255), unique=True, index=True, nullable=True)  # nullable for flexibility
    picture    = Column(String(512), nullable=True)   # Google profile photo URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    resumes          = relationship("Resume",          back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription",  back_populates="user", cascade="all, delete-orphan")
    interviews       = relationship("Interview",       back_populates="user", cascade="all, delete-orphan")


# ── B. Resumes ────────────────────────────────────────────────────────────────

class Resume(Base):
    __tablename__ = "resumes"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_filename  = Column(String(512), nullable=False)        # original filename shown in UI
    file_path        = Column(String(512), nullable=False)        # server storage path / S3 key
    file_type        = Column(SAEnum(FileType), nullable=False)   # pdf | docx | txt
    text_content     = Column(Text)                               # parsed raw text (for RAG)
    extracted_skills = Column(JSON)                               # ["Python", "FastAPI", ...]
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    user       = relationship("User",        back_populates="resumes")
    chunks     = relationship("ResumeChunk", back_populates="resume", cascade="all, delete-orphan")
    interviews = relationship("Interview",   back_populates="resume")
    ats_reports= relationship("ATSReport",   back_populates="resume")


# ── B1. Resume Chunks (for RAG pipeline) ─────────────────────────────────────

class ResumeChunk(Base):
    """
    Stores individual text chunks used by FAISS / Qdrant.
    Lets you reindex without re-uploading the file.
    chunk_index = order within the resume (0, 1, 2 ...)
    qdrant_id   = the point ID in your Qdrant collection (nullable until indexed)
    """
    __tablename__ = "resume_chunks"

    id          = Column(Integer, primary_key=True, index=True)
    resume_id   = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text        = Column(Text, nullable=False)
    qdrant_id   = Column(String(64))   # store as string; Qdrant uses UUID point IDs

    resume = relationship("Resume", back_populates="chunks")


# ── C. Job Descriptions ───────────────────────────────────────────────────────

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title              = Column(String(255))                # "Software Engineer at Google"
    content            = Column(Text, nullable=False)       # full JD text
    extracted_keywords = Column(JSON)                       # ["REST API", "Docker", ...]
    created_at         = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    user        = relationship("User",        back_populates="job_descriptions")
    interviews  = relationship("Interview",   back_populates="job_description")
    ats_reports = relationship("ATSReport",   back_populates="job_description")


# ── D. Interview Sessions ─────────────────────────────────────────────────────

class Interview(Base):
    __tablename__ = "interviews"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id",            ondelete="CASCADE"), nullable=False, index=True)
    resume_id      = Column(Integer, ForeignKey("resumes.id",          ondelete="SET NULL"), nullable=True)
    job_id         = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    status         = Column(SAEnum(InterviewStatus), default=InterviewStatus.in_progress, nullable=False)
    overall_score  = Column(Float)                         # 0.0 – 100.0; null until completed
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    completed_at   = Column(DateTime(timezone=True))

    # relationships
    user            = relationship("User",           back_populates="interviews")
    resume          = relationship("Resume",         back_populates="interviews")
    job_description = relationship("JobDescription", back_populates="interviews")
    qa_logs         = relationship("QALog",          back_populates="interview", cascade="all, delete-orphan")


# ── E. Questions & Answers ────────────────────────────────────────────────────

class QALog(Base):
    __tablename__ = "qa_logs"

    id           = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    question     = Column(Text, nullable=False)
    user_answer  = Column(Text)
    ai_feedback  = Column(Text)
    score        = Column(Float)    # per-question score; 0.0 – 10.0
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    interview = relationship("Interview", back_populates="qa_logs")


# ── F. ATS Reports ────────────────────────────────────────────────────────────

class ATSReport(Base):
    __tablename__ = "ats_reports"

    id               = Column(Integer, primary_key=True, index=True)
    resume_id        = Column(Integer, ForeignKey("resumes.id",          ondelete="CASCADE"),  nullable=False, index=True)
    job_id           = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    match_score      = Column(Float, nullable=False)    # 0.0 – 100.0  ← the headline number
    missing_keywords = Column(JSON)                     # ["Kubernetes", "CI/CD", ...]
    suggestions      = Column(Text)                     # AI-generated improvement text
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    resume          = relationship("Resume",         back_populates="ats_reports")
    job_description = relationship("JobDescription", back_populates="ats_reports")