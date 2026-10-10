<div align="center">

# 🔍 CareerLens AI

### Full-Stack AI Career Coaching Platform — Resume Gap Analyzer & Mock Interview Coach

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF69B4?style=for-the-badge)](https://www.trychroma.com/)
[![Langchain](https://img.shields.io/badge/LangChain-Integration-1C3C3C?style=for-the-badge)](https://www.langchain.com/)
[![Groq](https://img.shields.io/badge/Groq-Fast_Inference-F55036?style=for-the-badge)](https://groq.com/)

<br/>

> **CareerLens AI** is a production-grade, full-stack AI platform that gives job seekers a measurable edge — combining a ChromaDB-backed RAG pipeline, semantic document chunking, ATS analysis, skill gap detection, and a multi-turn AI interview coach.

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🧠 RAG Pipeline Deep Dive](#-rag-pipeline-deep-dive)
- [🗂️ Project Structure](#️-project-structure)
- [🗄️ Database Schema](#️-database-schema)
- [🔌 API Reference](#-api-reference)
- [⚙️ Setup & Installation](#️-setup--installation)
- [🐳 Docker Deployment](#-docker-deployment)
- [🔐 Environment Variables](#-environment-variables)
- [🛠️ Tech Stack](#️-tech-stack)

---

## ✨ Features

### 📄 ATS Score Analyzer
Upload your resume and paste a job description to get a detailed ATS compatibility report. CareerLens identifies keyword matches, formatting issues, and skills alignment gaps to maximize your chances of passing automated screening systems.

### 🎤 AI Mock Interview Coach
An interactive, multi-turn AI interviewer that simulates real interview scenarios. Supports multiple categories:
- **Behavioural** — STAR method coaching and situational questions
- **System Design** — Architecture, scalability, and tradeoff discussions
- **DSA / Python** — Algorithmic problem-solving with code walkthroughs
- **ML / AI** — Model evaluation, MLOps, and deep learning concepts
- **Backend / FastAPI & SQL** — API design, query optimization, ORM patterns

### 🔍 Job Gap Analyzer
Compares your resume against a target job description using a strict ChromaDB RAG pipeline. Highlights missing skills, under-represented experience, and generates a prioritized roadmap for closing gaps.

### ⚡ Semantic Document Chunking
Powered by LangChain and OpenAI, documents are intelligently split along percentile-based semantic breakpoints instead of fixed lengths, ensuring that complete thoughts and bullet points are successfully captured.

### 📊 Personalized Dashboard
Tracks career readiness over time:
- Latest uploaded resume & job description with persistent context bar
- Mock interview history with per-session scores
- ATS match scores across multiple job applications
- AI-generated profile improvement suggestions with progressive feature unlocking

### 🔐 Google OAuth + JWT Authentication
One-click Google sign-in with secure JWT session management via Authlib. User profiles, documents, interview history, and analysis reports are all persisted in PostgreSQL with a fully normalized 7-table schema.

---

## 🏗️ Architecture

```
                        ┌──────────────────────────────────────────┐
                        │           Browser / Client                │
                        │  (Jinja2 UI — Glassmorphism, Drag & Drop)│
                        └────────────────┬─────────────────────────┘
                                         │ HTTP / REST
                        ┌────────────────▼─────────────────────────┐
                        │           FastAPI Application             │
                        │  (lifespan, JWT middleware, CORS, routing)│
                        └──┬──────────┬─────────────┬──────────────┘
                           │          │             │
          ┌────────────────▼──┐  ┌────▼──────┐  ┌──▼────────────────┐
          │   Auth Routes     │  │  Semantic │  │   AI / LLM Routes │
          │  /auth/login      │  │  RAG      │  │  /chat  /ats      │
          │  /auth/callback   │  │  Pipeline │  │  /interview       │
          │  /auth/me         │  │           │  │  /gap_analysis    │
          └────────┬──────────┘  └───┬───────┘  └──────────┬────────┘
                   │                 │                     │
          ┌────────▼──────┐  ┌───────▼───────────┐  ┌──────▼────────────┐
          │  PostgreSQL   │  │  ChromaDB         │  │   LLM Inference   │
          │  SQLAlchemy   │  │  LangChain        │  │   Groq / OpenAI   │
          │  (7 tables)   │  │  (Vector Store)   │  │                   │
          └───────────────┘  └───────────────────┘  └───────────────────┘
```

---

## 🧠 RAG Pipeline Deep Dive

CareerLens uses a focused semantic retrieval pipeline powered by **LangChain** and **ChromaDB**.

### 1. Document Ingestion & Parsing
- Resume (PDF/DOCX/TXT) texts are extracted using heavy-duty parsers like `pdfplumber` and `pypdf`.
- The extracted documents are processed by LangChain's **`SemanticChunker`**, which leverages `text-embedding-3-small` to split text smoothly across logical document breakpoints, securing context integrity.

### 2. Embedded Storage
- The vectorized chunks, packed with robust metadata (e.g., `user_id`, `type`, `resume_id`, `jd_id`), are pushed asynchronously to a standalone **ChromaDB HTTP server** (`localhost:8001`) preventing database locks.

### 3. Query & Retrieval
- CareerLens initiates semantic similarity searches using optimized queries on the vector store, pulling the top contextual chunks from the specific user's resume and target job description context. The contexts are natively deduplicated.

### 4. Lightning Inference via Groq
- The assembled knowledge base is sent natively over high-speed inference endpoints like Groq (or OpenAI) to orchestrate complex chains: **ATS Scorer**, **Gap Analyzer**, or the **Interview Coach** evaluating responses.

---

## 🗂️ Project Structure

```
CareerLens/
│
├── app/
│   ├── main.py                      # FastAPI app — lifespan, middleware, routers
│   │
│   ├── routes/
│   │   └── api/
│   │       ├── auth.py              # Google OAuth login, Authlib implementation
│   │       ├── routes.py            # /chat, /ats, /interview, /gap_analysis
│   │       ├── upload.py            # Resume (PDF/TXT) & JD uploading
│   │       └── chroma_proxy.py      # Secure UI proxy for ChromaDB integration
│   │
│   ├── rag/
│   │   ├── ingestion_pipeline.py    # LangChain SemanticChunker → ChromaDB ingestion
│   │   └── query_pipeline.py        # Vector Similarity Search + deduplication
│   │
│   ├── services/
│   │   ├── gap_analyzer.py          # Gap analysis business logic layer
│   │   └── resume_analyze.py        # Resume analysis logic
│   │
│   ├── db/
│   │   ├── database.py              # SQLAlchemy engine (PostgreSQL)
│   │   ├── session.py               # get_db dependency
│   │   ├── models.py                # ORM models (User, Resume, JobDescription, etc.)
│   │   └── schemas.py               # Pydantic validation schemas
│   │
│   ├── utils/                       # Shared configuration utilities
│   └── templates/                   # Jinja2 HTML templates
│
├── uploads/                         # Stored resume files
├── chroma_data/                     # ChromaDB persistent storage directory
│
├── .env                             # Secret API keys
├── requirements.txt                 # Python dependencies
└── pyproject.toml                   # Project metadata
```

---

## 🗄️ Database Schema

CareerLens relies on a structured **PostgreSQL** backend modeled via SQLAlchemy.

```
users
├── id, name, email, google_id, picture, created_at
│
├── resumes (1:many)
│   ├── id, user_id, upload_filename, file_path, file_type
│   ├── text_content          
│   ├── extracted_skills (JSON)
│   ├── ats_reports (1:many)  
│   └── gap_reports (1:many)  
│
├── job_descriptions (1:many)
│   ├── id, user_id, title, company, content
│   ├── extracted_keywords (JSON)
│   └── created_at
│
└── interviews (1:many)
    ├── id, user_id, resume_id, job_id, category, status, overall_score
    ├── created_at, completed_at
    └── qa_logs (1:many)
        ├── question, user_answer, ai_feedback, score
        └── created_at
```

---

## 🔌 API Reference

### Authentication — `/auth`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/auth/login` | Renders the login page |
| `GET` | `/auth/login/google` | Initiates Google OAuth redirect |
| `GET` | `/auth/callback/google` | Handles OAuth callback, issues session cookie |
| `GET` | `/auth/me` | Returns current user profile |
| `POST` | `/auth/logout` | Clears the session logic |

### Document Upload — `/upload`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload/resume` | Upload document, triggering LangChain Chunker + ChromaDB |
| `POST` | `/upload/job-description` | Save document text, triggering integration |

### AI Features — `/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat`  | General AI career coach chat |
| `POST` | `/interview` | Mock interview session (multi-turn) |
| `POST` | `/ats` | ATS score analysis |
| `POST` | `/gap_analysis` | Job gap analysis via Chroma RAG |

---

## ⚙️ Setup & Installation

### Prerequisites
- Python **3.10+**
- **PostgreSQL** instance (local or remote)
- A **Google Cloud** project (for OAuth 2.0 Client Credentials)
- **OpenAI API Key** (for text embeddings)
- **Groq API Key** (optional but highly recommended for fast chat inference)

### 1. Clone & Environment
```bash
git clone https://github.com/sinuarlowbaby/CareerLens-AI.git
cd CareerLens-AI
python -m venv .venv
.venv\Scripts\activate on Windows # Or source .venv/bin/activate 

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create `.env` in the root folder:
```bash
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SECRET_KEY=long_random_session_secret
DATABASE_URL=postgresql://user:password@localhost:5432/careerlens
```

### 3. Initialize the Databases
```bash
alembic upgrade head
```

### 4. Run the Application
The `main.py` explicitly launches ChromaDB automatically, followed by your FastAPI server.
```bash
uvicorn app.main:app --reload
```

---

## ☁️ AWS & Docker Deployment
CareerLens is fully configured for containerized hosting on AWS (EC2, Lightsail, ECS Fargate, or App Runner).

To launch locally or on an EC2 instance with Docker Compose:
```bash
docker compose up -d --build
```
For complete step-by-step AWS deployment options, RDS setup, and SSL configuration, see the [AWS Deployment Guide](aws_deployment_guide.md).

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance Async HTTP Framework |
| **Templating** | [Jinja2](https://jinja.palletsprojects.com/) | Server HTML Rendering (Glassmorphism UI) |
| **ORM / Database**| [SQLAlchemy](https://sqlalchemy.org) + PostgreSQL | Relational storage schema modeling |
| **Auth** | [Authlib](https://docs.authlib.org/) | Deep-integrated Google OAuth & Sessions |
| **Vector Database** | [ChromaDB](https://www.trychroma.com/) | Fast similarity vector text search |
| **LLM Agents** | [LangChain](https://www.langchain.com/) | Complex chunking and retriever pipelining |
| **Embeddings** | OpenAI `text-embedding-3-small` | Contextual semantic vectorization |
| **Inference Models**| [Groq](https://groq.com/) & OpenAI | Low-latency LLM evaluation & coaching |
| **PDF Extraction**| `pdfplumber` & `pypdf` | Strict resume context mining |

---

<div align="center">

*Built as an end-to-end operational portfolio project using an agile AI tech stack.*

</div>
