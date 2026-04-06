# import json
# from app.llm.llm_client import call_llm


# async def calculate_ats_score(resume: str, job: str):
#     prompt = f"""
#     Analyze resume vs job description.

#     Return JSON:
#     {{
#         "score": 0-100,
#         "matched_skills": [],
#         "missing_skills": [],
#         "suggestions": []
#     }}

#     Resume:
#     {resume}

#     Job:
#     {job}
#     """

#     response = await call_llm(prompt)

#     try:
#         return json.loads(response)
#     except:
#         return {
#             "score": 50,
#             "matched_skills": [],
#             "missing_skills": [],
#             "suggestions": [response]
#         }