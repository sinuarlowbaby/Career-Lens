from langchain_openai import OpenAIEmbeddings
from app.models.user import User
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
    

async def query_pipeline(user_query: str, user_id :str,resume_id: int, jd_id: int , top_k: int):
    query_embedding = get_embedding(user_query)
    all_resume = vector_store.similarity_search(
        query_embedding,
        k=top_k,
        filter={"user_id": user_id, "type": "resume", "resume_id": resume_id}
    )
    all_jd = vector_store.similarity_search(
        query_embedding,
        k=top_k,
        filter={"user_id": user_id, "type": "job_description", "jd_id": jd_id}
    )
    resume_docs, jd_docs = deduplicate_docs(all_resume , all_jd)

    return resume_docs, jd_docs
    