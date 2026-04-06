<div align="center">

# 🔍 CareerLens AI

### Full-Stack AI Career Coaching Platform — Resume Gap Analyzer & Mock Interview Coach

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-GAN_Chunker-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Redis](https://img.shields.io/badge/Redis-Semantic_Cache-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-00A3E0?style=for-the-badge)](https://github.com/facebookresearch/faiss)

<br/>

> **CareerLens AI** is a production-grade, full-stack AI platform that gives job seekers a measurable edge — combining a hybrid RAG pipeline, GAN-inspired keyword extraction, ATS analysis, skill gap detection, and a multi-turn AI interview coach.

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
Compares your resume against a target job description using a hybrid FAISS + BM25 RAG pipeline with CrossEncoder reranking. Highlights missing skills, under-represented experience, and generates a prioritized roadmap for closing gaps.

### ⚡ GAN-Inspired Keyword Chunking *(Technical Differentiator)*
A custom PyTorch module inspired by GAN-style adversarial training generates and refines keyword chunks from resume and JD text — surfacing domain-specific skills that standard NLP chunkers miss.

### 📊 Personalized Dashboard
Tracks career readiness over time:
- Latest uploaded resume & job description with persistent context bar
- Mock interview history with per-session scores
- ATS match scores across multiple job applications
- AI-generated profile improvement suggestions with progressive feature unlocking

### 🔐 Google OAuth + JWT Authentication
One-click Google sign-in with secure JWT session management. User profiles, documents, interview history, and analysis reports are all persisted in PostgreSQL with a fully normalized 7-table schema.

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
          │   Auth Routes     │  │  Hybrid   │  │   AI / LLM Routes │
          │  /auth/login      │  │  RAG      │  │  /chat  /ats      │
          │  /auth/callback   │  │  Pipeline │  │  /interview       │
          │  /auth/me         │  │           │  │  /gap_analysis    │
          └────────┬──────────┘  └───┬───────┘  └──────────┬────────┘
                   │                 │                      │
          ┌────────▼──────┐  ┌───────▼───────────┐  ┌──────▼────────────┐
          │  PostgreSQL   │  │  FAISS + BM25     │  │   LLM Inference   │
          │  SQLAlchemy   │  │  CrossEncoder     │  │   Groq / OpenAI   │
          │  (7 tables)   │  │  Redis Sem. Cache │  │   (Embeddings)    │
          └───────────────┘  └───────────────────┘  └───────────────────┘
                                      ▲
                             ┌────────┴──────────┐
                             │  PyTorch GAN      │
                             │  Keyword Chunker  │
                             └───────────────────┘
```

---

## 🧠 RAG Pipeline Deep Dive

CareerLens uses a custom hybrid retrieval pipeline — no LangChain dependency.

### 1. Ingestion
- Resume (PDF/DOCX/TXT) and job description are split using a **GAN-inspired keyword chunker** (PyTorch) for domain-aware chunking, supplemented by semantic splitting.
- Chunks are embedded via `text-embedding-3-small` and stored in **FAISS** with rich metadata (`user_id`, `type`, `resume_id`, `jd_id`).
- BM25 index is built in parallel over the same corpus for lexical retrieval.

### 2. Query — Hybrid Retrieval
- At query time, **HyDE (Hypothetical Document Embeddings)** expands the query before retrieval — a hypothetical ideal answer is generated and embedded to improve semantic match quality.
- Results from **FAISS** (dense) and **BM25** (sparse) are fused using Reciprocal Rank Fusion (RRF).
- A **CrossEncoder reranker** scores candidate chunks for final top-k selection.

### 3. Semantic Caching
- Query embeddings are checked against **Redis** before hitting the retrieval stack. Semantically similar queries are served from cache, reducing latency and LLM cost.

### 4. Generation
- The reranked context is passed to the appropriate LLM prompt chain: **ATS Scorer**, **Gap Analyzer**, or **Interview Coach**.

```
User Query
   │
   ▼
HyDE Query Expansion ──► Embed expanded query
   │
   ├──► FAISS dense search ──┐
   │                         ├──► RRF Fusion ──► CrossEncoder Rerank ──► Top-K Context ──► LLM
   └──► BM25 lexical search ─┘
         ▲
   Redis Semantic Cache (hit → skip retrieval)
```

---

## 🗂️ Project Structure

```
CareerLens/
│
├── app/
│   ├── main.py                      # FastAPI app — lifespan, middleware, router registration
│   │
│   ├── routes/
│   │   └── api/
│   │       ├── auth.py              # Google OAuth login, JWT creation/validation, /me endpoint
│   │       ├── routes.py            # /chat, /ats, /interview, /gap_analysis endpoints
│   │       ├── upload.py            # Resume (PDF/DOCX/TXT) & JD upload/ingestion
│   │       └── ai.py                # Supplementary AI utility endpoints
│   │
│   ├── rag/
│   │   ├── ingestion_pipeline.py    # GAN chunking → FAISS + BM25 embedding & storage
│   │   ├── query_pipeline.py        # HyDE, hybrid retrieval, RRF, reranking, deduplication
│   │   ├── gan_chunker.py           # PyTorch GAN-inspired keyword chunking module
│   │   └── semantic_cache.py        # Redis-based semantic query cache
│   │
│   ├── llm/
│   │   ├── llm_client.py            # Groq / OpenAI client initialization and abstraction
│   │   ├── ats_score.py             # ATS scoring prompt chain
│   │   ├── gap_analyzer.py          # Job gap analysis prompt chain
│   │   ├── question_generator.py    # Interview question generation prompt chain
│   │   └── answer_evaluation.py     # Answer evaluation & scoring prompt chain
│   │
│   ├── services/
│   │   ├── auth_service.py          # JWT decode → get_current_user dependency
│   │   ├── ats_score.py             # ATS business logic layer
│   │   ├── gap_analyzer.py          # Gap analysis business logic layer
│   │   └── chat_service.py          # Chat / interview session orchestration
│   │
│   ├── db/
│   │   ├── database.py              # SQLAlchemy engine & Base setup (PostgreSQL)
│   │   ├── session.py               # get_db dependency (session per request)
│   │   ├── models.py                # ORM models: User, Resume, JobDescription, Interview,
│   │   │                            #   QALog, ATSReport, GapReport
│   │   └── schemas.py               # Pydantic request/response schemas
│   │
│   ├── utils/                       # Helper utilities and shared configuration
│   └── templates/                   # Jinja2 HTML templates (glassmorphism UI)
│
├── uploads/                         # Stored resume files (server-side)
├── faiss_index/                     # FAISS persistent index directory
│
├── .env                             # Secret keys and API credentials (not committed)
├── Dockerfile                       # Container image definition
├── docker-compose.yaml              # Multi-service orchestration (app + Redis)
├── requirements.txt                 # All Python dependencies (pinned)
└── pyproject.toml                   # Project metadata
```

---

## 🗄️ Database Schema

CareerLens uses **PostgreSQL** via SQLAlchemy ORM with a fully normalized 7-table schema.

```
users
├── id, name, email, google_id, picture, created_at
│
├── resumes (1:many)
│   ├── id, user_id, upload_filename, file_path, file_type
│   ├── text_content          ← parsed raw text for RAG ingestion
│   ├── extracted_skills (JSON)
│   ├── ats_reports (1:many)  ← match_score, missing_keywords, suggestions
│   └── gap_reports (1:many)  ← gap_summary, priority_roadmap, missing_skills (JSON)
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
| `GET` | `/auth/callback/google` | Handles OAuth callback, issues JWT |
| `GET` | `/auth/me` | Returns current user profile + latest resume/JD |
| `POST` | `/auth/logout` | Stateless JWT logout (client clears token) |

### Document Upload — `/upload`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload/resume` | Upload resume (PDF / DOCX / TXT), triggers GAN chunking + FAISS/BM25 ingestion |
| `POST` | `/upload/job-description` | Save job description text, triggers embedding pipeline |

### AI Features — `/`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/chat` | ❌ | General AI career coach chat |
| `POST` | `/interview` | ❌ | Mock interview session (multi-turn) |
| `POST` | `/ats` | ✅ | ATS score analysis — resume vs. JD |
| `POST` | `/gap_analysis` | ✅ | Job gap analysis via hybrid RAG pipeline |
| `GET` | `/health` | ❌ | API health check |

> 📖 Full interactive docs available at **`http://localhost:8000/docs`** (Swagger UI)

---

## ⚙️ Setup & Installation

### Prerequisites
- Python **3.10+**
- [`uv`](https://astral.sh/uv) — ultra-fast Python package manager
- **PostgreSQL** instance (local or cloud)
- **Redis** instance (local or cloud — for semantic caching)
- A **Google Cloud** project with OAuth 2.0 credentials
- An **OpenAI** API key (for embeddings + LLM)
- A **Groq** API key (for fast inference — optional but recommended)

---

### 1. Clone the Repository

```bash
git clone https://github.com/sinuarlowbaby/CareerLens-AI.git
cd CareerLens-AI
```

### 2. Install `uv` (if not already installed)

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create Virtual Environment & Install Dependencies

```bash
uv venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

uv pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root. See the [Environment Variables](#-environment-variables) section for the full list.

```bash
# Minimum required to start
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SECRET_KEY=your_random_jwt_secret
DATABASE_URL=postgresql://user:password@localhost:5432/careerlens
REDIS_URL=redis://localhost:6379
```

### 5. Initialize the Database

```bash
# Run Alembic migrations (or SQLAlchemy create_all on first run)
uv run alembic upgrade head
```

### 6. Run the Application

```bash
uv run uvicorn app.main:app --reload
```

| Service | URL |
|---------|-----|
| 🌐 **App UI** | http://localhost:8000 |
| 📖 **Swagger Docs** | http://localhost:8000/docs |

---

## 🐳 Docker Deployment

The `docker-compose.yaml` orchestrates the FastAPI app, PostgreSQL, and Redis:

```bash
# Build and launch all services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

> ⚠️ Make sure your `.env` file is present in the project root before running Docker Compose — it is loaded automatically by the compose file.

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
# ── Required ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...                      # OpenAI API key (embeddings + LLM)
GOOGLE_CLIENT_ID=...                       # Google OAuth Client ID
GOOGLE_CLIENT_SECRET=...                   # Google OAuth Client Secret
SECRET_KEY=your_random_jwt_secret          # JWT signing secret (use a long random string)
DATABASE_URL=postgresql://user:pw@host/db  # PostgreSQL connection string

# ── Redis (Semantic Cache) ─────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379           # Redis connection URL

# ── Optional ──────────────────────────────────────────────────────────────────
GROQ_API_KEY=gsk_...                       # Groq API key for fast LLM inference
FRONTEND_URL=http://localhost:8000         # Redirected to after OAuth login
ALLOWED_ORIGINS=http://localhost:8000      # Comma-separated CORS origins
FAISS_INDEX_PATH=./faiss_index             # FAISS index storage path
CACHE_SIMILARITY_THRESHOLD=0.92           # Redis cache hit threshold (cosine similarity)
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn | Async HTTP server & REST API |
| **Templating** | [Jinja2](https://jinja.palletsprojects.com/) | Server-rendered HTML frontend (glassmorphism UI) |
| **ORM / DB** | [SQLAlchemy](https://sqlalchemy.org) + PostgreSQL | Relational data storage (7-table schema) |
| **Auth** | [Authlib](https://docs.authlib.org/) + Google OAuth + JWT | SSO authentication & session management |
| **Dense Retrieval** | [FAISS](https://github.com/facebookresearch/faiss) | High-speed vector similarity search |
| **Sparse Retrieval** | BM25 (rank-bm25) | Lexical keyword retrieval |
| **Reranking** | CrossEncoder (sentence-transformers) | Precision reranking of retrieved chunks |
| **Query Expansion** | HyDE | Hypothetical Document Embeddings for better recall |
| **Semantic Cache** | [Redis](https://redis.io) | Query-level semantic caching to reduce latency & cost |
| **GAN Chunker** | [PyTorch](https://pytorch.org) | Adversarially-trained keyword chunk generator |
| **Embeddings** | OpenAI `text-embedding-3-small` | Document & query vectorization |
| **LLM Inference** | [Groq](https://groq.com/) / [OpenAI](https://openai.com/) | ATS scoring, gap analysis, interview chat |
| **PDF Parsing** | [pdfplumber](https://github.com/jsvine/pdfplumber) + pypdf | Resume text extraction |
| **Packaging** | [uv](https://astral.sh/uv) | Fast Python environment management |
| **Containerization** | Docker + Docker Compose | Deployment orchestration |

---

<div align="center">

*Built as a portfolio-grade AI system — production architecture, not a prototype.*

</div>
