import os
import chromadb
from dotenv import load_dotenv
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from sqlalchemy.orm import Session

load_dotenv()

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
CHROMA_HOST     = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT     = int(os.getenv("CHROMA_PORT", "8001"))

import logging

logger = logging.getLogger(__name__)

# 1. Initialize the embedding function once
embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)

def init_chroma_client():
    """
    Connects to Chroma HTTP server if available;
    falls back to local PersistentClient so the app never crashes at boot.
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        client.heartbeat()
        logger.info(f"[Chroma] Connected to Chroma HTTP server at {CHROMA_HOST}:{CHROMA_PORT}")
        return client
    except Exception as e:
        logger.warning(
            f"[Chroma] Could not connect to Chroma HTTP server at {CHROMA_HOST}:{CHROMA_PORT} ({e}). "
            f"Using local PersistentClient (path='./chroma_data')."
        )
        return chromadb.PersistentClient(path="./chroma_data")

class LazyVectorStore:
    """Proxy object that delays Chroma vector store initialization until first access."""
    def __init__(self):
        self._store = None

    def _get_store(self):
        if self._store is None:
            client = init_chroma_client()
            self._store = Chroma(
                client=client,
                embedding_function=embedder,
                collection_name="career_lens",
            )
        return self._store

    def __getattr__(self, name):
        return getattr(self._get_store(), name)

vector_store = LazyVectorStore()

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