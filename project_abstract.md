# Project Abstract: CareerLens AI

## 1. Context and Background
In the highly competitive modern job market, candidates face significant challenges in securing early-stage interviews. The recruitment process is heavily guarded by Applicant Tracking Systems (ATS) that filter resumes based on rigid keyword matching and structural parameters. Furthermore, technical candidates must pass robust multi-stage interviews encompassing algorithm design, system architecture, and behavioral assessments. Traditional preparation methods rely on generic online resources or expensive human coaching, leaving many job seekers with a critical lack of personalized, actionable feedback to improve their candidacies.

## 2. Problem Statement
Job seekers frequently lack visibility into how their resumes align with specific job descriptions, often resulting in automated rejections due to hidden skill gaps or poor formatting. Even when candidates successfully secure an interview, they often struggle to articulate their experiences using structured methodologies or find it difficult to simulate high-pressure technical and behavioral interviews on demand. There is a need for a comprehensive, intelligent platform that can accurately diagnose application deficiencies and provide targeted, interactive interview preparation.

## 3. Proposed Solution
**CareerLens AI** is a production-grade, full-stack AI career coaching platform designed to give job seekers a measurable edge. The platform addresses the job application pipeline holistically by combining document parsing, semantic analysis, and conversational AI into a unified workflow. CareerLens allows candidates to evaluate their resumes against specific job descriptions to uncover ATS compatibility scores and skill gaps. Additionally, it features an interactive, multi-turn AI Mock Interview Coach capable of simulating domain-specific technical and behavioral interviews.

## 4. Methodology and Architecture
CareerLens utilizes an efficient, simplified Retrieval-Augmented Generation (RAG) architecture powered by modern AI developer tools:
*   **Intelligent Ingestion & Chunking:** Resumes and job descriptions are processed and split contextually using LangChain's SemanticChunker. By utilizing OpenAI's `text-embedding-3-small`, the chunking algorithm accurately splits documents at percentile-based semantic breakpoints rather than arbitrary text lengths.
*   **Vector Retrieval:** The system employs ChromaDB as its core vector store, allowing for fast, low-latency similarity searches when querying the user's specific career history against job requirements.
*   **LLM Inference:** Complex AI analysis—such as ATS scoring, gap analysis, and interview simulations—is powered by the high-speed Groq API and OpenAI models, enabling near-instant conversational feedback. 
*   **Full-Stack Ecosystem:** The backend is built using FastAPI and a relational PostgreSQL database managed via SQLAlchemy, handling secure Google OAuth + JWT authentication (powered by Authlib). The frontend is cleanly implemented using Jinja2 templates for a responsive, glassmorphism-inspired UI.

## 5. Key Features and Outcomes
*   **ATS Score Analyzer & Job Gap Analyzer:** Accurately retrieves and compares your skills, responsibilities, and competencies against job requirements, generating a prioritized roadmap to close skill gaps.
*   **Domain-Specific AI Mock Interviewer:** Simulates deep, multi-turn interviews across categories including Behavioral, System Design, DSA/Python, ML/AI, and Backend Engineering.
*   **Personalized Analytics Dashboard:** Tracks career readiness over time, persisting document context, interview history, and user authentication seamlessly.

By synthesizing clean semantic chunking, efficient vector search, and conversational agents, CareerLens AI provides an accessible and robust coaching experience, closing the gap between candidate potential and hiring expectations.
