from langchain_openai import OpenAIEmbeddings
from app.db.models import User
from app.rag.ingestion_pipeline import vector_store

embedder = OpenAIEmbeddings(model="text-embedding-3-small")

def get_embedding(user_query: str):
    return embedder.embed_query(user_query)

def deduplicate_docs(docs_resume, docs_jd):
    seen = set()
    unique_resume_docs = []
    unique_jd_docs = []
    for doc in docs_resume:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            unique_resume_docs.append(doc)

    for doc in docs_jd:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            unique_jd_docs.append(doc)
    return unique_resume_docs, unique_jd_docs
    

from app.services.gap_analyzer import analyze_gap_ai

async def query_pipeline(user_query: str, user_id :str,resume_id: int, jd_id: int , top_k: int):
    all_resume = vector_store.similarity_search(
        user_query,
        k=top_k,
        filter={"$and": [{"user_id": user_id}, {"type": "resume"}, {"resume_id": resume_id}]}
    )
    all_jd = vector_store.similarity_search(
        user_query,
        k=top_k,
        filter={"$and": [{"user_id": user_id}, {"type": "job_description"}, {"jd_id": jd_id}]}
    )
    resume_docs, jd_docs = deduplicate_docs(all_resume , all_jd)

    return resume_docs, jd_docs

async def gap_analysis_pipeline(user_id: int, resume_id: int, jd_id: int):
    # Retrieve documents relevant to skills, experience, and qualifications
    comprehensive_query = "skills, work experience, responsibilities, education, qualifications, core competencies, achievements"
    
    # Get top 15 chunks to form a good context for gap analysis
    all_resume = vector_store.similarity_search(
        comprehensive_query,
        k=15,
        filter={"$and": [{"user_id": user_id}, {"type": "resume"}, {"resume_id": resume_id}]}
    )
    all_jd = vector_store.similarity_search(
        comprehensive_query,
        k=15,
        filter={"$and": [{"user_id": user_id}, {"type": "job_description"}, {"jd_id": jd_id}]}
    )
    
    resume_docs, jd_docs = deduplicate_docs(all_resume, all_jd)
    
    # Combine chunks to string
    resume_text = "\n".join([doc.page_content for doc in resume_docs])
    jd_text = "\n".join([doc.page_content for doc in jd_docs])
    
    # Await AI response
    gap_analysis_result = await analyze_gap_ai(resume_text, jd_text)
    
    return {
        "gap_analysis": gap_analysis_result
    }