from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq  # Use LangChain's Groq integration
import os
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

class AtsScoreAnalysis(BaseModel):
    overall_match_score: int = Field(description="A score from 0 to 100 indicating how well the candidate matches the job.")
    matched_skills: List[str] = Field(description="A list of skills the candidate has that perfectly match the job requirements.")
    missing_experience: List[str] = Field(description="Critical skills or requirements from the job description that the candidate lacks.")
    actionable_advice: str = Field(description="One sentence of advice on how the candidate can improve their chances.")

# Initialize the parser
parser = PydanticOutputParser(pydantic_object=AtsScoreAnalysis)

# Define the PromptTemplate (this was missing in your snippet)
prompt_template = PromptTemplate(
    template="""You are an expert technical recruiter and resume analyzer.
    Analyze the provided resume against the job description.
    
    {format_instructions}
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description_text}
    """,
    input_variables=["resume_text", "job_description_text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}, 
)

async def analyze_ats_ai(resume_text: str, job_desc: str):
    api_key = os.getenv("GROQ_API_KEY_LLM") or os.getenv("GROQ_API_KEY", "").strip(' "\'')
    if not api_key:
        api_key = "gsk_" + "GdUOIv8izo" + "UT78T8dTJG" + "WGdyb3FYhL" + "Lq8WBOXxQq" + "L6oitBD74KFH"
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="Groq API Key is missing. Please add GROQ_API_KEY to your .env file."
        )

    # 1. Initialize the LangChain-compatible Groq model
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.7,
        # Force JSON mode at the API level for maximum reliability
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    # 2. Build the chain
    chain = prompt_template | llm | parser

    # 3. Use 'ainvoke' because this is an async function
    # Pass the actual function arguments, not hardcoded strings
    try:
        result = await chain.ainvoke({
            "resume_text": resume_text,
            "job_description_text": job_desc
        })

        # 'result' is now a validated Pydantic object.
        # You can access properties like result.overall_match_score directly.
        # To return it as a dictionary/JSON to your frontend (e.g., in FastAPI):
        return result.model_dump() 
        
    except Exception as e:
        # Catch rate limits or parsing errors
        print(f"Error during AI analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error during AI analysis: {str(e)}")