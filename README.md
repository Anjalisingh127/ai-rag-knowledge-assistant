# AI-Enabled RAG Knowledge Assistant

A technical-support knowledge assistant built to retrieve relevant incident,
runbook and FAQ content, produce grounded answers, preserve source traceability,
and measure retrieval quality.

> **Project status:** active implementation. Core ingestion, FAISS retrieval,
> grounded generation, evaluation, FastAPI endpoints and Streamlit UI are
> implemented. Docker/deployment and final benchmark publication come after
> local validation.

## Why I built it

Support teams often search across incident records and troubleshooting
documentation before deciding what to check next. This project models that
workflow with a focused RAG pipeline rather than sending an unsupported prompt
directly to an LLM.

Example:

```text
Question
  -> normalize
  -> retrieve top-K knowledge chunks
  -> check whether evidence is sufficient
  -> build traceable context
  -> generate/extract grounded answer
  -> return source metadata
  -> log timing / evaluate retrieval
```

All operational records in this repository are synthetic.

## Tech stack

- Python 3.12
- FastAPI + Pydantic
- LangChain components
- FAISS
- local Sentence Transformers or OpenAI embeddings
- context-only, OpenAI or Ollama generation
- Streamlit
- pytest + Ruff
- GitHub Actions

## Knowledge base

The repository currently covers:

- HTTP 503 / service availability
- database timeouts and connection issues
- authentication failures
- slow API responses
- network and DNS connectivity
- application-support escalation and validation guidance

Data lives under `data/` as structured incidents, Markdown runbooks, an FAQ
and a curated retrieval-evaluation set.

## Project structure

```text
app/
  api/            FastAPI routes, schemas and dependencies
  core/           configuration, exceptions and structured logging
  evaluation/     retrieval metrics and evaluation runner
  ingestion/      loaders and chunking pipeline
  rag/            embeddings, FAISS, retrieval, context and generation

data/
  incidents/
  runbooks/
  faq/
  evaluation/

scripts/
  build_index.py
  run_evaluation.py
  test_local_retrieval.py

tests/
docs/
```

See [architecture](docs/architecture.md), [evaluation](docs/evaluation.md) and
[limitations](docs/limitations.md) for engineering details.

## Local setup

### 1. Clone

```bash
git clone https://github.com/Anjalisingh127/ai-rag-knowledge-assistant.git
cd ai-rag-knowledge-assistant
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install

For tests/API development without downloading a transformer model:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

For the free local transformer embedding provider:

```bash
pip install -e ".[dev,local]"
```

### 4. Configure environment

```powershell
Copy-Item .env.example .env
```

The default configuration uses local embeddings and the deterministic
context-only generator. No paid LLM API is required for tests or retrieval
evaluation.

## Build the FAISS index

With the local optional dependencies installed:

```bash
python scripts/build_index.py
```

The generated index is stored under `vector_store/` and is intentionally
ignored by Git.

## Run retrieval evaluation

```bash
python scripts/run_evaluation.py
```

The report is written to `reports/retrieval_metrics.json`. Metrics are not
claimed in this README until they are measured from a validated run.

## Run tests

```bash
pytest
```

Lint:

```bash
ruff check .
```

## Run the API

```bash
uvicorn app.api.app:app --reload
```

OpenAPI docs are available locally at `/docs`.

Implemented endpoints:

- `GET /health`
- `POST /api/retrieve`
- `POST /api/query`
- `GET /api/sources`
- `POST /api/evaluate`

## Run the Streamlit UI

Start the API first, then in another terminal:

```bash
streamlit run app/streamlit_app.py
```

## Provider configuration

The application supports separate embedding and generation choices through
environment variables.

Embeddings:

- `local` - Sentence Transformers, free/local after model download
- `openai` - optional OpenAI embeddings

Generation:

- `context` - deterministic extractive fallback for free demos and tests
- `openai` - optional OpenAI chat model
- `ollama` - optional local Ollama model

API keys are read only from environment configuration and `.env` is ignored.

## Evaluation

The project measures retrieval separately from generation. The current
evaluation code calculates Hit Rate@K, Recall@K and MRR and records failed
queries for inspection.

This is deliberate: a statement such as “95% RAG accuracy” is not meaningful
without a defined metric and dataset.

## CI

GitHub Actions runs Ruff and pytest on pushes and pull requests to `main`.
The local transformer model is not downloaded in CI because automated tests use
a deterministic offline embedding implementation.

## Limitations

This is a portfolio-scale system built over synthetic operational data. It is
not connected to a real production ticketing platform, and the local FAISS
index is not a distributed search service. See [docs/limitations.md](docs/limitations.md).

## Roadmap

Next validated stages:

1. run the complete local quality gate and record the actual baseline;
2. improve retrieval only where the evaluation identifies real failures;
3. add Docker;
4. deploy the API/UI;
5. publish measured metrics and demo screenshots.

## License

MIT.
