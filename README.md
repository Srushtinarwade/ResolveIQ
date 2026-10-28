# ResolveIQ — AI-Powered ServiceNow Resolution Engine

ResolveIQ is an AI-assisted incident and change-request resolution service built with **FastAPI**, **LangGraph**, **Google Gemini**, **PostgreSQL**, and **pgvector**. It accepts ServiceNow ticket webhooks, summarizes the reported issue, retrieves similar historical resolutions, generates a proposed resolution plan, and can post that plan back to the originating ticket.


> **Reported evaluation snapshot:** **85% resolution success across 200 held-out IT tickets** (equivalent to 170 successful tickets out of 200). This is a reported result; the repository does not currently include the ticket-level evaluation sheet needed to independently reproduce it.

## Evaluation Methodology

The success rate should be calculated against a fixed set of **200 held-out IT tickets** that were not used to build or tune the system:

1. Generate a proposed resolution for each ticket using the same configured workflow.
2. Compare each generated resolution with a verified reference resolution.
3. Score each response against a predefined rubric covering **correctness, relevance, completeness, and safety**. Count a ticket as successful only when it meets the rubric's pass criteria.
4. Calculate the overall success rate:

   \\[ \\text{Success Rate}=\\frac{\\text{Successfully evaluated tickets}}{200}\\times100\\% \\]

For example, if 170 of the 200 tickets pass all required rubric criteria, the success rate is **85%**. To make the reported result reproducible, publish an anonymized score sheet with per-ticket pass/fail outcomes, the rubric, and the reference/evaluation procedure. Do not include confidential ServiceNow ticket text or credentials.

## How It Works

```text
ServiceNow Webhook
        |
        v
  FastAPI + Pydantic
        |
        v
  LangGraph Workflow
  1. Summarize ticket with Gemini
  2. Retrieve similar resolved tickets from pgvector
  3. Generate a proposed resolution with Gemini
  4. Post the plan to ServiceNow
        |
        v
ServiceNow work note
```

## Core Components

| Component | Purpose |
|---|---|
| FastAPI | Exposes webhook and ingestion endpoints |
| Pydantic | Validates and structures incoming ticket data |
| LangGraph | Orchestrates the ticket-analysis workflow |
| Google Gemini | Summarizes tickets and drafts proposed resolutions |
| PostgreSQL + pgvector | Stores embeddings and retrieves similar historical tickets |
| ServiceNow REST API | Receives the proposed resolution as a work note |
| LangSmith | Provides tracing and observability hooks |

## Data Ingestion

ResolveIQ can ingest resolved incidents and change requests. The ingestion flow summarizes each resolved ticket and stores the resulting text with relevant metadata in the vector database. This historical knowledge is used as retrieval context when a new ticket is analyzed.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/incident/new` | Accepts a new incident for analysis |
| `POST` | `/change/new` | Accepts a new change request for analysis |
| `POST` | `/incident/resolved` | Ingests a resolved incident |
| `POST` | `/change/resolved` | Ingests a resolved change request |
| `POST` | `/ingest/batch` | Accepts a batch of resolved tickets |

The webhook routes use a shared dependency for request verification. Configure the matching secret and credentials in your local environment before testing integrations.

## Project Structure

```text
now-resolve/
├── main.py
├── dependencies.py
├── graph/
│   └── workflow.py
├── nodes/
│   ├── summarize_ticket_node.py
│   ├── retrieve_historical_context_node.py
│   ├── generate_resolution_node.py
│   └── post_result_to_servicenow_node.py
├── models/
│   └── ticket_models.py
├── routers/
│   ├── analyze.py
│   └── ingest.py
├── states/
│   └── analyzer_state.py
├── utils/
│   ├── db_utils.py
│   ├── insert_ticket_util.py
│   ├── checkpointer.py
│   └── logging_config.py
├── Dockerfile
└── requirements.txt
```

## Prerequisites

- Python 3.13 or a compatible version for the pinned dependencies
- Docker
- A Google Gemini API key
- A PostgreSQL database with pgvector
- A ServiceNow instance and credentials for end-to-end integration testing

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Srushtinarwade/ResolveIQ.git
cd ResolveIQ
python -m venv .venv
```

Activate the virtual environment:

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### 2. Start PostgreSQL with pgvector

For local experimentation, you can start a PostgreSQL container with the pgvector image:

```bash
docker run -d \
  --name resolveiq-db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=change_me \
  -e POSTGRES_DB=analyzer \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

Use a non-default password in any environment that is not disposable. If you already have a PostgreSQL/pgvector instance, use its connection string instead.

### 3. Configure environment variables

Create a local `.env` file in the project root. Keep real credentials out of source control.

```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://admin:change_me@localhost:5432/analyzer

SNOW_INSTANCE=your_instance_name
SNOW_USERNAME=your_username
SNOW_PASSWORD=your_password

# Set this if required by the webhook verification dependency:
WEBHOOK_SECRET=your_webhook_secret
```

Use the exact environment-variable names expected by the code and your ServiceNow configuration. Do not commit API keys, passwords, tokens, or production credentials.

### 4. Run the API

```bash
uvicorn main:app --reload
```

When the service starts successfully, the API is normally available at `http://localhost:8000`; FastAPI's interactive documentation is at `http://localhost:8000/docs`.

## Deployment

### Docker

Build the image:

```bash
docker build -t resolveiq .
```

Run it with environment variables supplied from your local environment file:

```bash
docker run --env-file .env -p 8000:8000 resolveiq
```

### Google Cloud Run

The application can be containerized for Cloud Run. Configure secrets and environment variables in the deployment environment before exposing any webhook endpoint. Review authentication and access controls before enabling unauthenticated access.

## Security Notes

- Keep `.env` and all credentials out of Git.
- Replace example database credentials before use beyond local experimentation.
- Restrict webhook access using the configured verification dependency.
- Use least-privilege ServiceNow credentials and rotate secrets if they are exposed.

## Technology Stack

- [FastAPI](https://fastapi.tiangolo.com/) — web API framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) — stateful workflow orchestration
- [Google Gemini](https://ai.google.dev/) — language model for ticket summarization and resolution drafting
- [PostgreSQL](https://www.postgresql.org/) and [pgvector](https://github.com/pgvector/pgvector) — persistent vector retrieval
- [LangChain](https://python.langchain.com/) — LLM and embedding integrations
- [Pydantic](https://docs.pydantic.dev/) — data validation
- [LangSmith](https://www.langchain.com/langsmith) — tracing and observability

## Notes

ResolveIQ generates **proposed** resolutions to support incident handling; validate generated plans before relying on them for operational changes. Actual end-to-end behavior depends on valid configuration, reachable external services, and appropriate ServiceNow permissions.
