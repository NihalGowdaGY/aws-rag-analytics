# AWS Contract Audit - RAG Q&A System with Analytics

A RAG (Retrieval-Augmented Generation) system that answers questions about the AWS Customer Agreement, built with a FastAPI backend, FAISS vector search, Gemini LLM, and a Streamlit dashboard. Every query is logged to SQLite and surfaced through a live analytics panel.

---

## What this does

- Parses and chunks the AWS Customer Agreement PDF into searchable text blocks
- Converts each chunk into vector embeddings using `sentence-transformers`
- On a user query, finds the top 3 most relevant chunks via FAISS similarity search
- Passes those chunks as context to Gemini 2.5 Flash to generate a grounded answer
- Refuses to guess if the answer isn't in the document, it says so explicitly
- Logs every query, response, latency, and context flag to a local SQLite database
- Exposes query analytics (most frequent questions, unanswered rate, average latency) via a REST endpoint

---

## Project structure

```
aws-rag-analytics/
├── app/
│   └── frontend.py          # Streamlit dashboard UI
├── src/
│   ├── backend.py           # FastAPI routes (/ingest, /ask, /analytics)
│   ├── rag_engine.py        # PDF parsing, FAISS indexing, LLM generation
│   ├── database.py          # SQLAlchemy engine and session setup
│   ├── models.py            # QueryLog ORM model
│   ├── schemas.py           # Pydantic request/response schemas
│   └── config.py            # Centralised settings (chunk size, model names, paths)
├── data/
│   └── AWS Customer Agreement.pdf
├── .env                     # Your API key goes here (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

**Prerequisites:** Python 3.10+

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/NihalGowdaGY/aws-rag-analytics.git
cd aws-rag-analytics

python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install python-dotenv
```

> Note: `python-dotenv` is used in `config.py` to load your API key  install it separately until the next requirements update.

### 3. Add your API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_google_ai_studio_key_here
```

Get a free key at [aistudio.google.com](https://aistudio.google.com).

---

## Running the app

You need two terminals running simultaneously.

**Terminal 1 - start the FastAPI backend:**

```bash
uvicorn src.backend:app --reload
```

Backend runs at `http://localhost:8000`. You can explore the API docs at `http://localhost:8000/docs`.

**Terminal 2 - start the Streamlit frontend:**

```bash
streamlit run app/frontend.py
```

Dashboard opens automatically at `http://localhost:8501`.

**First thing to do:** 
Click the **"Initialize Document Ingestion Pipeline"** button on the dashboard. This parses the PDF, generates embeddings, and persists the data assets to disk. Thanks to local file caching, these will auto-reload on subsequent startups without re-running ingestion.
---

## API endpoints

| Method | Endpoint | What it does |
|--------|----------|-------------|
| `POST` | `/ingest` | Parses the PDF and builds the FAISS vector index |
| `POST` | `/ask` | Accepts a query, runs RAG, returns answer + source chunks + logs the interaction |
| `GET` | `/analytics` | Returns aggregated query stats from the SQLite database |

### Example - ask a question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What interest rate does AWS charge on late payments?"}'
```

Response:

```json
{
  "query": "What interest rate does AWS charge on late payments?",
  "answer": "AWS may charge interest at 1.5% per month on late payments...",
  "sources": ["...relevant contract text..."],
  "latency_seconds": 1.243
}
```

---

## Design decisions

### Chunking strategy - size 1000, overlap 200

Legal contracts are dense. A single clause often bundles definitions, exceptions, and financial terms together. A 1000-character chunk is large enough to keep a full clause intact rather than splitting it mid-sentence. The 200-character overlap acts as a safety bridge if a critical term or exception sits right at a chunk boundary, the overlap ensures it appears in at least one complete chunk, so the retrieval doesn't miss it.

### Top-k retrieval - k = 3

Three chunks gives roughly 3000 characters of contract context per query. That's enough to resolve cross-referenced clauses (for example, matching a late payment question with its penalty exception in a different section) without bloating the prompt or slowing down generation.

### Embeddings - `all-MiniLM-L6-v2`

Lightweight, fast, and runs entirely locally with no API costs. Produces 384-dimensional vectors that work well for semantic similarity on legal text. FAISS with a flat L2 index handles exact nearest neighbour search appropriate for a corpus this size (the AWS agreement is a single document).

### LLM - Gemini 2.5 Flash

Fast inference, strong instruction following, and handles structured system prompts reliably. Temperature is set to `0.0` for fully deterministic answers important for a compliance use case where you don't want the model paraphrasing contract terms in ways that might change their meaning.

### Hallucination guardrail

The system prompt instructs the model to rely only on the provided context and return a fixed fallback phrase if the answer isn't there. This phrase is detected on the backend to set the `context_found = False` flag in the database, which feeds directly into the unanswered query count on the analytics dashboard.

---

## Analytics dashboard

The telemetry panel (right side of the dashboard) shows:

- **Total queries logged** - all-time request count
- **Out-of-scope fallbacks** - queries where no relevant context was found
- **Mean pipeline latency** - average end-to-end response time in seconds
- **Top query trends** - most frequently asked questions

You can also use the **"Populate Metrics Logs"** button to auto-fire 30 test queries (a mix of on-topic contract questions and intentionally out-of-scope ones like weather and sports) to seed the analytics panel with realistic data.

---

## Database schema

Every call to `/ask` is logged to `query_analytics.db`:

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Unique request ID |
| `query_text` | String | The user's question |
| `generated_response` | String | The LLM's answer |
| `context_found` | Boolean | True if contract context was retrieved, False for out-of-scope |
| `latency_seconds` | Float | End-to-end response time |
| `timestamp` | DateTime | UTC timestamp of the request |