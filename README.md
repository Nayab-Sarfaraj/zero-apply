<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/ZeroApply-000000?style=for-the-badge&logoColor=white">
  <img alt="ZeroApply" src="https://img.shields.io/badge/ZeroApply-ffffff?style=for-the-badge&logoColor=black">
</picture>

**AI-Powered Automated Resume Screening & Candidate Evaluation Pipeline**

FastAPI · LangChain · Groq LLM · ARQ Async Workers · PostgreSQL · PyMuPDF

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-1.4+-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://langchain.com)
[![Groq](https://img.shields.io/badge/Groq-Qwen_3.8_27B-F55036?style=flat-square)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat-square)](https://sqlalchemy.org)
[![ARQ Queue](https://img.shields.io/badge/ARQ-Redis_Queue-DC382D?style=flat-square&logo=redis&logoColor=white)](https://arq-docs.helpmanual.io)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1.28+-2BA84A?style=flat-square)](https://pymupdf.readthedocs.io)
[![uv](https://img.shields.io/badge/uv-Package_Manager-DE5FE9?style=flat-square)](https://github.com/astral-sh/uv)

</div>

---

## What it does

**ZeroApply** is an asynchronous, high-throughput talent screening engine. Recruiters post job descriptions with explicit required skills, nice-to-have qualifications, and minimum experience thresholds. Candidates submit their applications alongside PDF resumes.

Instead of waiting synchronously on heavy LLM inference, FastAPI dispatches background screening tasks to an **ARQ** queue backed by **Redis**. An autonomous background worker extracts full text from the resume using **PyMuPDF (`fitz`)**, constructs a specialized evaluation prompt, and invokes **Groq's ultra-low-latency LLM** (`qwen/qwen3.8-27b`) with strict **Pydantic structured output**.

The engine computes an objective composite screening score based on deterministic requirement match evidence and experience weighting, extracting candidate strengths, skill gaps, and actionable hiring recommendations directly into **PostgreSQL**.

---

## Architecture

The following diagram illustrates the end-to-end architecture across client interactions, API routing, asynchronous job dispatching, background worker processing, and database persistence:

```mermaid
graph TB
    subgraph Client["Client & Recruiter"]
        Swagger["Swagger UI / OpenAPI\n/docs"]
        Recruiter["Recruiter / ATS Client\nHTTP JSON / Multipart"]
    end

    subgraph FastAPIApp["FastAPI Application (Port 8000)"]
        Lifespan["Lifespan Manager\nRedis Connection Pool"]
        API_Jobs["Job Endpoints\nPOST /jobs\nGET /jobs\nGET /jobs/:id"]
        API_Candidates["Candidate Endpoints\nPOST /jobs/:id/candidates\nGET /jobs/:id/candidates\nGET /candidates/:id"]
        API_Screen["Screening Dispatcher\nPOST /candidates/:id/screen\nGET /candidates/:id/screening"]
    end

    subgraph Queue["Async Task Queue"]
        RedisQueue[("Redis 7.0+\nPort 6379\nARQ Job Queue")]
    end

    subgraph WorkerService["Background Worker (ARQ Process)"]
        ARQWorker["ARQ Worker Consumer\nWorkerSettings"]
        PDFParser["PyMuPDF (fitz)\nHigh-Speed PDF Text Extractor"]
        ScoringEngine["Scoring Engine\nFormula Weighted Evaluator"]
    end

    subgraph AIEngine["AI & LLM Layer (Groq Cloud)"]
        GroqModel["Groq API\nqwen/qwen3.8-27b"]
        LangChainChain["LangChain LCEL Chain\nPromptTemplate | with_structured_output"]
        StructuredOutput["Pydantic ScreeningOutput\nMatches + Strengths + Evidence"]
    end

    subgraph Storage["Persistence & Storage Layer"]
        LocalFS["Local Storage\nuploads/*.pdf"]
        Postgres[("PostgreSQL 16\nPort 5433\njobs, candidates, screenings")]
    end

    Recruiter -->|1. Create job posting| API_Jobs
    API_Jobs -->|Insert Job record| Postgres
    Recruiter -->|2. Submit candidate + PDF| API_Candidates
    API_Candidates -->|Save raw PDF bytes| LocalFS
    API_Candidates -->|Insert Candidate status=applied| Postgres
    Recruiter -->|3. Trigger screening| API_Screen
    API_Screen -->|Enqueue screen_candidate_job| RedisQueue
    RedisQueue -->|Dequeue job payload| ARQWorker
    ARQWorker -->|Read candidate & job spec| Postgres
    ARQWorker -->|Stream PDF file bytes| LocalFS
    ARQWorker -->|Parse raw text| PDFParser
    PDFParser -->|Inject resume text| LangChainChain
    LangChainChain -->|Structured inference request| GroqModel
    GroqModel -->|Validated JSON response| StructuredOutput
    StructuredOutput -->|Compute score| ScoringEngine
    ScoringEngine -->|Persist score & analysis| Postgres
    Recruiter -->|4. Poll / fetch screening report| API_Screen
    API_Screen -->|Read latest evaluation| Postgres

    style Client fill:#1a1a2e,stroke:#6366f1,color:#e2e8f0
    style FastAPIApp fill:#0f172a,stroke:#3b82f6,color:#e2e8f0
    style Queue fill:#1a0a00,stroke:#f97316,color:#e2e8f0
    style WorkerService fill:#1e1b4b,stroke:#8b5cf6,color:#e2e8f0
    style AIEngine fill:#261300,stroke:#f55036,color:#e2e8f0
    style Storage fill:#0a1a0a,stroke:#22c55e,color:#e2e8f0
```

---

## Candidate & Screening Status Flow

Candidates transition through a recruitment lifecycle, while their automated evaluations are processed asynchronously via ARQ:

```mermaid
stateDiagram-v2
    [*] --> applied : Candidate uploaded with PDF resume

    state "Screening Task (ARQ)" as ScreeningTask {
        [*] --> queued : POST /candidates/:id/screen
        queued --> processing : Worker dequeues candidate_id
        processing --> completed : Groq structured output parsed & saved
        processing --> failed : File missing or LLM rate limit
        failed --> queued : Auto-retry / re-enqueue
    }

    applied --> shortlisted : High composite score & match evidence
    applied --> rejected : Low match score / missing mandatory skills
    shortlisted --> interviewing : Recruiter schedules technical interview
    interviewing --> hired : Offer extended & accepted
    interviewing --> rejected : Post-interview rejection
    hired --> [*]
    rejected --> [*]
```

---

## Core Pipeline — Step by Step

The sequence below details the interaction flow between the Recruiter, FastAPI application, Redis queue, background ARQ worker, Groq AI, and PostgreSQL:

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter / ATS
    participant API as FastAPI (main.py)
    participant FS as Local Storage (/uploads)
    participant DB as PostgreSQL 16
    participant Redis as Redis (ARQ Queue)
    participant Worker as ARQ Worker (worker.py)
    participant Fitz as PyMuPDF (fitz)
    participant Groq as Groq (Qwen 3.8 27B)

    Recruiter->>API: POST /jobs (title, description, required_skills, min_experience)
    API->>DB: INSERT INTO jobs
    DB-->>API: Job created (id=1)
    API-->>Recruiter: 201 Created (job details)

    Recruiter->>API: POST /jobs/1/candidates (name="Jane Doe", file=resume.pdf)
    Note over API,FS: Stream and persist PDF safely to disk
    API->>FS: Write bytes to uploads/resume.pdf
    API->>DB: INSERT INTO candidates (job_id=1, resume_url, status='applied')
    DB-->>API: Candidate created (id=42)
    API-->>Recruiter: 201 Created (candidate details)

    Recruiter->>API: POST /candidates/42/screen
    API->>DB: Verify candidate exists
    API->>Redis: enqueue_job("screen_candidate_job", candidate_id=42)
    API-->>Recruiter: 200 OK {"status": "queued", "job_id": "arq:..."}

    Note over Redis,Worker: Asynchronous Execution Boundary
    Redis->>Worker: Dispatch screen_candidate_job(candidate_id=42)
    Worker->>DB: SELECT candidate & job specifications
    Worker->>FS: Open uploads/resume.pdf
    Worker->>Fitz: fitz.open(resume_url) & extract page text
    Fitz-->>Worker: Clean extracted plain text
    Worker->>Groq: ainvoke(PromptTemplate | model.with_structured_output(ScreeningOutput))
    Note over Groq: Qwen-3.8-27b evaluates skill evidence & experience match
    Groq-->>Worker: Validated Pydantic ScreeningOutput object
    Worker->>Worker: Calculate required_score & experience_score
    Worker->>DB: INSERT INTO screenings (candidate_id, score, strengths, weaknesses, recommendation)
    DB-->>Worker: Screening record committed

    Recruiter->>API: GET /candidates/42/screening
    API->>DB: SELECT latest screening WHERE candidate_id=42
    DB-->>API: Screening record
    API-->>Recruiter: 200 OK (score, strengths, weaknesses, match evidence)
```

---

## Scoring Engine & Evaluation Formula

ZeroApply uses an objective, evidence-driven evaluation formula to calculate candidate scores without subjective drift:

```mermaid
graph LR
    subgraph Inputs["LLM Structured Evaluation"]
        M["Requirement Matches\n(matched: bool, evidence: str)"]
        E["Experience Match\n(percentage: 0 - 100%)"]
    end

    subgraph Calculation["Scoring Weights"]
        R_Score["Required Skills Score\n(Matches / Total) × 60 pts"]
        E_Score["Experience Score\nMatch% × 0.25 (max 25 pts)"]
    end

    subgraph Output["Composite Evaluation"]
        FinalScore["Screening Score\n(0 to 85+ points)"]
        Qualitative["Qualitative Feedback\nStrengths + Weaknesses + Recommendation"]
    end

    M --> R_Score
    E --> E_Score
    R_Score --> FinalScore
    E_Score --> FinalScore
    FinalScore --> Qualitative
```

### Mathematical Formula

$$\text{Required Score} = \left( \frac{\sum \text{Matched Required Skills}}{\text{Total Required Skills}} \right) \times 60$$

$$\text{Experience Score} = \text{Experience Match Percentage} \times 0.25$$

$$\text{Composite Score} = \text{Required Score} + \text{Experience Score}$$

### Evaluation Components

| Component                 | Max Points        | Description                                                                                        |
| ------------------------- | ----------------- | -------------------------------------------------------------------------------------------------- |
| **Required Skills Match** | **60.0**          | Proportional score computed from verified skill requirements supported by resume evidence.         |
| **Experience Match**      | **25.0**          | Scaled percentage measuring candidate's career longevity against the job's minimum years required. |
| **Nice-To-Have Skills**   | _Bonus / Context_ | Matched non-mandatory skills recorded to help break ties between top candidates.                   |
| **Evidence Validation**   | _Audit Trail_     | Each skill match includes direct text excerpts from the resume preventing hallucinations.          |

---

## API Endpoints Reference

Interactive documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

### Core Routes

| Method | Endpoint                               | Status        | Description                                           |
| ------ | -------------------------------------- | ------------- | ----------------------------------------------------- |
| `GET`  | `/`                                    | `200 OK`      | Server health check endpoint                          |
| `POST` | `/jobs`                                | `201 Created` | Create a new job opening                              |
| `GET`  | `/jobs`                                | `200 OK`      | Retrieve all job listings                             |
| `GET`  | `/jobs/{job_id}`                       | `200 OK`      | Retrieve single job by ID                             |
| `POST` | `/jobs/{job_id}/candidates`            | `201 Created` | Submit candidate application (`name` + PDF upload)    |
| `GET`  | `/jobs/{job_id}/candidates`            | `200 OK`      | List all candidates for a specific job                |
| `GET`  | `/candidates/{candidate_id}`           | `200 OK`      | Retrieve candidate details and status                 |
| `POST` | `/candidates/{candidate_id}/screen`    | `200 OK`      | Enqueue background AI resume screening job            |
| `GET`  | `/candidates/{candidate_id}/screening` | `200 OK`      | Retrieve latest screening score and evaluation report |
| `POST` | `/upload`                              | `200 OK`      | Standalone file upload helper endpoint                |
| `GET`  | `/uploads`                             | `200 OK`      | PDF text extraction preview helper                    |

---

### Request & Response Examples

#### 1. Create a Job Posting

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Backend Engineer",
    "description": "Building high-throughput microservices, background job queues, and LLM pipelines.",
    "min_experience": 4,
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    "nice_to_have": ["Docker", "LangChain", "Kubernetes"]
  }'
```

**Response (`201 Created`):**

```json
{
  "id": 1,
  "title": "Senior Python Backend Engineer",
  "description": "Building high-throughput microservices, background job queues, and LLM pipelines.",
  "min_experience": 4,
  "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
  "nice_to_have": ["Docker", "LangChain", "Kubernetes"]
}
```

#### 2. Submit Candidate with PDF Resume

```bash
curl -X POST http://localhost:8000/jobs/1/candidates \
  -F "name=Alex Mercer" \
  -F "file=@/path/to/resume.pdf"
```

**Response (`201 Created`):**

```json
{
  "id": 1,
  "name": "Alex Mercer",
  "job_id": 1,
  "resume_url": "uploads/resume.pdf",
  "status": "applied",
  "created_at": "2026-09-30T11:22:00.000000"
}
```

#### 3. Trigger Asynchronous Screening

```bash
curl -X POST http://localhost:8000/candidates/1/screen
```

**Response (`200 OK`):**

```json
{
  "message": "Screening started",
  "job_id": "8f481c00-d872-4d74-90aa-62725fa1b2e9",
  "status": "queued"
}
```

#### 4. Fetch Candidate Screening Results

```bash
curl -X GET http://localhost:8000/candidates/1/screening
```

**Response (`200 OK`):**

```json
{
  "id": 1,
  "candidate_id": 1,
  "score": 75.0,
  "strengths": [
    "5+ years developing async APIs using FastAPI and Python",
    "Extensive experience with PostgreSQL query tuning and indexing",
    "Hands-on background designing distributed task queues in Redis"
  ],
  "weaknesses": ["Limited production Kubernetes cluster administration noted"],
  "recommendation": "Strong candidate. Matches all required technical criteria with solid experience.",
  "experience_match_percentage": 100.0
}
```

---

## Project Structure

```
job-fastapi/
├── src/
│   └── job_fastapi/
│       ├── __init__.py                # Package entrypoint
│       ├── main.py                    # FastAPI application, routing, lifespan Redis pool
│       ├── worker.py                  # ARQ worker definition, PyMuPDF parsing, LangChain chain
│       │
│       ├── config/
│       │   └── database.py            # SQLAlchemy 2.0 engine, SessionLocal, get_db dependency
│       │
│       ├── models/                    # SQLAlchemy declarative ORM models
│       │   ├── job_mode.py            # Job model (PostgreSQL ARRAY columns for skills)
│       │   ├── candidate.py          # Candidate model with JobStatus enum
│       │   └── screening.py          # Screening model (score, strengths, weaknesses)
│       │
│       └── schema/
│           └── job.py                 # Pydantic schemas (Job, Candidate, ScreeningOutput)
│
├── uploads/                           # Local resume storage directory (.pdf)
├── Dockerfile                         # Container build definition (Python 3.13 + uv)
├── docker-compose.yaml                # PostgreSQL 16 + Redis 7 services
├── pyproject.toml                     # Project dependencies & scripts (managed via uv)
├── uv.lock                            # Deterministic dependency lockfile
├── .env.example                       # Environment configuration template
├── .env                               # Local secrets (ignored in git)
└── README.md                          # Project documentation
```

---

## Data Schemas & Contracts

The `ScreeningOutput` schema acts as the **contract** between the Groq LLM inference layer and the scoring persistence engine:

```python
# src/job_fastapi/schema/job.py
class RequirementMatch(BaseModel):
    skill: str
    matched: bool
    evidence: str | None = None

class ScreeningOutput(BaseModel):
    strengths: list[str] = Field(
        default_factory=list,
        description="The strengths of the candidate based on their resume"
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="The weaknesses or gaps in the candidate's resume"
    )
    requirement_matches: list[RequirementMatch] = Field(
        default_factory=list,
        description="Whether the candidate matches each job requirement, with supporting evidence"
    )
    recommendation: str = Field(
        description="Overall recommendation based on the candidate's resume and job requirements"
    )
    experience_match_percentage: float
    nice_to_have_matches: list[str] = Field(
        default_factory=list,
        description="Skills in nice-to-have section that candidate possesses"
    )
```

### Relational Entity Schema

```mermaid
erDiagram
    JOBS ||--o{ CANDIDATES : "receives"
    CANDIDATES ||--o{ SCREENINGS : "evaluated by"

    JOBS {
        int id PK
        string title
        string description
        int min_experience
        string_array required_skills
        string_array nice_to_have
        datetime created_at
    }

    CANDIDATES {
        int id PK
        int job_id FK
        string name
        string resume_url
        enum status "applied | shortlisted | interviewing | rejected | hired"
        datetime created_at
    }

    SCREENINGS {
        int id PK
        int candidate_id FK
        float score
        string_array strengths
        string_array weaknesses
        string recommendation
        float experience_match_percentage
    }
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure your credentials:

| Variable       | Description                                                 | Default / Example                                                   | Required |
| -------------- | ----------------------------------------------------------- | ------------------------------------------------------------------- | -------- |
| `DATABASE_URL` | PostgreSQL connection string (psycopg driver)               | `postgresql+psycopg://postgres:postgres@localhost:5433/job_fastapi` | **Yes**  |
| `GROQ_API_KEY` | API token from [console.groq.com](https://console.groq.com) | `gsk_...`                                                           | **Yes**  |
| `GROQ_MODEL`   | Fast LLM model deployed on Groq Cloud                       | `qwen/qwen3.8-27b`                                                  | No       |
| `REDIS_URL`    | Redis connection URI for ARQ task queue                     | `redis://localhost:6379`                                            | **Yes**  |
| `APP_ENV`      | Application environment mode                                | `development`                                                       | No       |
| `APP_HOST`     | Host address to bind the Uvicorn server                     | `0.0.0.0`                                                           | No       |
| `APP_PORT`     | Port number to bind the Uvicorn server                      | `8000`                                                              | No       |
| `LOG_LEVEL`    | Logging verbosity (`debug`, `info`, `warning`)              | `info`                                                              | No       |
| `SECRET_KEY`   | Cryptographic key for signatures and sessions               | `your-secret-key-here`                                              | No       |

---

## Local Development

### Prerequisites

- **Python 3.13+**
- [**uv**](https://github.com/astral-sh/uv) (Extremely fast Python package manager)
- **Docker & Docker Compose** (for PostgreSQL and Redis)

---

### Step-by-Step Setup

#### 1. Clone the repository

```bash
git clone https://github.com/Nayab-Sarfaraj/zero-apply.git
cd zero-apply
```

#### 2. Start PostgreSQL and Redis containers

```bash
docker compose up -d
```

Verify containers are running:

```bash
docker compose ps
```

- PostgreSQL is mapped to port `5433` on host (`5432` internal).
- Redis is mapped to port `6379` on host.

#### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and insert your `GROQ_API_KEY`.

#### 4. Install dependencies via `uv`

```bash
uv sync
```

#### 5. Start the FastAPI development server

```bash
uv run uvicorn job_fastapi.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

#### 6. Start the ARQ Background Worker

Open a separate terminal window and launch the worker process:

```bash
uv run arq job_fastapi.worker.WorkerSettings
```

The worker connects to Redis on `localhost:6379`, listens for `screen_candidate_job` events, and processes PDF resumes as tasks arrive.

---

## Key Implementation Notes

<details>
<summary><strong>Asynchronous Task Offloading with ARQ & Redis</strong></summary>

Resume parsing and LLM inference take between 1.5 to 4.0 seconds depending on document length and model load. Performing this work synchronously inside the HTTP request loop would exhaust ASGI worker pools and degrade API responsiveness.

Using **ARQ** (Async Redis Queue), `POST /candidates/{id}/screen` immediately yields a queued status code (`200 OK`) and pushes the task onto Redis. The dedicated ARQ worker processes jobs concurrently without blocking incoming user traffic.

</details>

<details>
<summary><strong>Strict Structured LLM Outputs via ChatGroq</strong></summary>

Rather than relying on brittle raw text prompts and regex parsing, the pipeline uses LangChain's `model.with_structured_output(ScreeningOutput)`.

Groq natively forces tool-calling / JSON schema adherence under the hood. The returned object is immediately validated against the `ScreeningOutput` Pydantic class, guaranteeing that fields like `requirement_matches`, `strengths`, and `experience_match_percentage` are always typed correctly.

</details>

<details>
<summary><strong>High-Performance PDF Text Extraction with PyMuPDF</strong></summary>

PDF parsing is executed via **PyMuPDF (`fitz`)**, a high-performance C-backed library. Compared to pure-Python parsers like `pypdf`, PyMuPDF processes multi-page PDF documents in single-digit milliseconds with superior extraction of multi-column layouts, tabular formatting, and custom fonts typically found in resumes.

</details>

<details>
<summary><strong>PostgreSQL Dialect Arrays with Psycopg 3</strong></summary>

Job skills (`required_skills`, `nice_to_have`) and screening outputs (`strengths`, `weaknesses`) are mapped directly to PostgreSQL native `ARRAY(String)` types using modern **SQLAlchemy 2.0 `Mapped` annotations**.

This eliminates redundant join tables for simple string tag collections while leveraging Psycopg 3's high-performance binary protocol (`psycopg[binary]`).

</details>

<details>
<summary><strong>FastAPI Lifespan Connection Pooling</strong></summary>

The application uses FastAPI's modern `@asynccontextmanager` lifespan handler to initialize the ARQ Redis connection pool on startup (`app.state.redis = await create_pool(...)`) and gracefully drain/close active connections on shutdown, preventing connection leaks.

</details>

<details>
<summary><strong>Anti-Hallucination Prompt Architecture</strong></summary>

The prompt in `worker.py` enforces strict grounding rules:

```text
Only use information present in the resume.
Do not invent experience.
```

Additionally, the `RequirementMatch` schema forces the LLM to supply direct textual `evidence` for every matched skill. If no supporting evidence exists in the resume text, the skill cannot be marked as matched.

</details>

---

## Tech Stack

| Component            | Technology                     | Rationale                                                                                         |
| -------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------- |
| **API Framework**    | FastAPI 0.141+                 | High performance async Python framework, automatic OpenAPI schema generation, Pydantic validation |
| **Task Queue**       | ARQ + Redis 7                  | Lightweight, fully async Python job queue with minimal overhead compared to Celery                |
| **LLM Provider**     | Groq Cloud                     | Ultra-low latency inference engine powered by custom LPU hardware                                 |
| **Model**            | `qwen/qwen3.8-27b`             | Advanced reasoning model capable of accurate structured skill extraction and scoring              |
| **AI Orchestration** | LangChain Core / Groq          | Clean LCEL pipeline composition with schema-enforced structured outputs                           |
| **PDF Extraction**   | PyMuPDF (`fitz`)               | Ultra-fast native C PDF rendering and text parsing                                                |
| **ORM & Database**   | SQLAlchemy 2.0 + PostgreSQL 16 | Robust relational persistence with native PostgreSQL array support and strict typing              |
| **DB Driver**        | Psycopg 3 Binary               | Next-generation Python PostgreSQL driver with async compatibility and binary wire protocol        |
| **Package Manager**  | `uv`                           | Astral's Rust-based Python package resolver providing sub-second virtualenv setups                |

---

## Product Limits & System Constraints

| Constraint               | Limit / Policy                              | Detail                                                                     |
| ------------------------ | ------------------------------------------- | -------------------------------------------------------------------------- |
| **Supported File Types** | `.pdf` only                                 | Checked via `file.content_type == "application/pdf"`                       |
| **Max Token Output**     | 2,048 tokens                                | Set on `ChatGroq(max_tokens=2048)` to bound inference cost                 |
| **LLM Timeout**          | 60 seconds                                  | Default ARQ job execution timeout                                          |
| **Database Port**        | `5433` (Host) $\rightarrow$ `5432` (Docker) | Configured in `docker-compose.yaml` to avoid conflicts with local Postgres |
| **Redis Port**           | `6379`                                      | Standard Redis port used by ARQ queue                                      |
| **Resume Storage**       | `uploads/` directory                        | Files saved locally with original filenames                                |

---

## Development Scripts & Cheatsheet

```bash
# Start Docker services (Postgres on 5433, Redis on 6379)
docker compose up -d

# Stop Docker services
docker compose down

# Sync dependencies using uv
uv sync

# Run FastAPI API server with auto-reload
uv run uvicorn job_fastapi.main:app --reload --port 8000

# Run ARQ background worker
uv run arq job_fastapi.worker.WorkerSettings

# Inspect database using psql inside container
docker exec -it job_fastapi_db psql -U postgres -d job_fastapi
```

---

## Roadmap

- [x] **Phase 1: Core Engine**
  - [x] Job creation and candidate application endpoints
  - [x] Multi-part PDF resume upload & disk persistence
  - [x] Asynchronous task dispatching via ARQ & Redis
  - [x] Groq LLM structured screening evaluation (`qwen/qwen3.8-27b`)
  - [x] Composite score calculation and persistence in PostgreSQL

- [ ] **Phase 2: Enhanced Reliability & Storage**
  - [ ] Cloud object storage support (AWS S3 / Cloudflare R2) replacing local `uploads/`
  - [ ] Support for `.docx` and `.txt` resume formats
  - [ ] Real-time screening progress updates via WebSockets or Server-Sent Events (SSE)
  - [ ] Automatic candidate status update (`shortlisted` / `rejected`) based on score thresholds

- [ ] **Phase 3: ATS & Enterprise Features**
  - [ ] Recruiter authentication & role-based access control (OAuth2 / JWT)
  - [ ] Multi-tenant company workspaces
  - [ ] Batch resume upload and bulk screening
  - [ ] Custom weighting sliders per job for skill vs. experience score calculation
