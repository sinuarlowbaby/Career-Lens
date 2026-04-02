# Career Lens: AI-Powered Resume & Career Coach

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

## 📌 Overview
**Career Lens** is an AI-driven platform designed to help ambitious job seekers ace interviews, beat Applicant Tracking Systems (ATS), and close skill gaps. 
The system leverages Retrieval-Augmented Generation (RAG) and LLM-powered evaluations to provide personalized, instant feedback across various stages of the career and interview preparation journey.

---

## 🚀 Features

The application is structured around several core capabilities:

- **📄 ATS Score Analyzer**: Evaluates resumes against specific Job Descriptions. Provides a detailed breakdown of keyword matching, formatting, and skills alignment to maximize your chances of getting past the ATS filters.
- **🎤 Mock Interview Assistant**: An interactive AI chat interviewer trained on real interview patterns from top companies. Supports testing across topics like:
  - Behavioural
  - System Design
  - DSA/Python
  - ML/AI
  - Backend/FastAPI & SQL Databases
- **🔍 Job Gap Analyzer**: Compares a user's resume/profile to target job requirements, proactively highlighting missing skills and recommending improvement areas.
- **📊 Personalized Dashboard**: Tracks your recent mock interview performances, ATS scores across different job applications, and overall profile readiness.

---

## 🏗️ Architecture & Tech Stack

### Core Technologies
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) - High-performance, async-first Python framework.
- **Templating**: Jinja2 - For rendering the frontend dashboard and user interface.
- **AI & Integrations**: OpenAI Models, Tiktoken (for token limitations management in prompts).
- **Core Strategy**: RAG pipelines utilizing embedding models and robust retrieval systems.

### Directory Structure
```
app/
├── main.py                     # FastAPI application entrypoint and lifespan events
├── db/                         # Database models, connection handling, and Pydantic schemas
├── llm/                        # LLM prompting tools (question generation, ats scoring, gap analysis)
├── rag/                        # Data ingestion and query pipelines for contextual retrieval
├── routes/                     
│   └── api/                    # Application web routes (auth, chat, skill_gap, interview, upload)
├── services/                   # Core business logic mapping routes to the LLM/DB components
├── templates/                  # UI components (index.html, dashboards)
└── utils/                      # Helper methods and configurations
```

---

## ⚙️ Setup and Installation

### 1. Clone the repository and navigate to the root directory
```bash
git clone <repository_url>
cd "Career Lens"
```

### 2. Set up a Python Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt

freeze
pip freeze > requirements.txt

```

### 4. Environment Variables
Create a `.env` file in the root directory and configure your necessary API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the Application
Launch the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload
```
You should now see the application UI running at `http://localhost:8000`, and the Swagger API documentation at `http://localhost:8000/docs`.

---

## 🛣️ API Endpoints (Preview)

The application structures its core functionality across these main API domains:

- **`/auth`** (`app/routes/api/auth.py`): Handles Login, Registration, Logout, and Password Reset capabilities.
- **`/upload`** (`app/routes/api/upload.py`): Document intake for Resumes and Job Descriptions.
- **`/chat`**, **`/ats`**, **`/interview`**, **`/skill_gap`** (`app/routes/api/routes.py`): Direct interactions for the various assistant functionalities.

---

*Note: This architecture is a skeleton framework. Implementations inside `/services`, `/llm`, and `/rag` require integration of vector database endpoints and AI function calls.*
