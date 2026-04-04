import os
from dotenv import load_dotenv
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from langchain_chroma import Chroma
# from app.db.models import ResumeChunk

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"

# 1. Initialize the embedding function once
embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)

# 2. Initialize Chroma. It now knows exactly how to embed anything you give it.
vector_store = Chroma(
    persist_directory="./vector_store",
    embedding_function=embedder,
    collection_name="career_lens"
)

def chunks_docs(resume_content: str, job_description_content: str, user_id: str, resume_id: int, jd_id: int):
    text_splitter = SemanticChunker(
        embeddings=embedder,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=80, # Fixed parameter name
    )
    
    resume_chunks = text_splitter.create_documents(
        texts=[resume_content],
        metadatas=[{"user_id": user_id, "type": "resume", "resume_id": resume_id}]
    )
    
    job_description_chunks = text_splitter.create_documents(
        texts=[job_description_content],
        metadatas=[{"user_id": user_id, "type": "job_description", "jd_id": jd_id}]
    )
    
    return resume_chunks, job_description_chunks


async def ingestion_pipeline(db: Session, user_id: str, resume_content: str, job_description_content: str, resume_id: int, jd_id: int):
    # 1. Chunk the documents and attach all metadata
    resume_chunks, job_description_chunks = chunks_docs(
        resume_content, job_description_content, user_id, resume_id, jd_id
    )
    
    # 2. Use the Async versions (aadd_documents) to keep FastAPI blazing fast
    await vector_store.aadd_documents(documents=resume_chunks)
    await vector_store.aadd_documents(documents=job_description_chunks)
    
    return {"status": "success", "chunks_stored": len(resume_chunks) + len(job_description_chunks)}