# AI-Enabled RAG Knowledge Assistant

A portfolio-scale technical-support Retrieval-Augmented Generation (RAG) application built to search incident records, runbooks, and FAQs, retrieve relevant evidence, and return grounded answers with source traceability.

The project is designed around a practical support-engineering use case: before suggesting a troubleshooting action, the application retrieves evidence from a controlled knowledge base instead of relying on an unsupported model response.

> **Project status:** core RAG pipeline and retrieval evaluation are complete and validated locally. FastAPI and Streamlit application layers are implemented; end-to-end runtime validation, Docker, deployment, and final demo assets remain.

## Current results

The retrieval layer has been evaluated on a curated 30-query benchmark containing 25 answerable support questions and 5 unsupported questions.

| Retrieval strategy | Hit Rate@5 | Recall@5 | MRR | Answerable retrieval failures |
| --- | ---: | ---: | ---: | ---: |
| Deterministic hash baseline | 92% | 92% | 0.6013 | 2 |
| MiniLM semantic embeddings | **100%** | **100%** | **0.9200** | **0** |

The comparison uses the same knowledge corpus, evaluation questions, and Top-K value. Evaluation files are intentionally excluded from the searchable corpus to prevent benchmark leakage.

These numbers measure **retrieval quality**, not end-to-end “RAG accuracy.”

## Why I built it

Technical-support work often involves searching incident history and troubleshooting documentation before deciding what to investigate next. I built this project to model that workflow while learning how a RAG application can be structured, tested, measured, and exposed as a usable service.

The design focuses on:

- local/free execution for the main portfolio workflow;
- source-aware retrieval and grounded responses;
- measurable retrieval quality rather than vague accuracy claims;
- separation between ingestion, retrieval, generation, API, and UI layers;
- deterministic tests that do not require a paid API;
- explicit handling of unsupported questions.

All operational records included in this repository are synthetic.

## Architecture

```text
                    Knowledge Sources
              incidents / runbooks / FAQ
                         |
                         v
              +----------------------+
              | Ingestion Pipeline   |
              | loaders + chunking   |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | Embedding Layer      |
              | MiniLM / OpenAI      |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | FAISS Vector Store   |
              +----------+-----------+
                         |
User Question ----------+
                         v
              +----------------------+
              | Vector Retriever     |
              | Top-K + metadata     |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | Evidence / Context   |
              | sufficiency check    |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | Generation Layer     |
              | context/OpenAI/Ollama|
              +----------+-----------+
                         |
                         v
              Grounded Answer + Sources
                         |
              +----------+-----------+
              |                      |
              v                      v
         FastAPI API            Streamlit UI
```

The evaluation pipeline is kept separate from the searchable knowledge base:

```text
data/evaluation/
      |
      v
Evaluation Runner
      |
      +--> Hash baseline
      |
      +--> MiniLM semantic retrieval
      |
      v
Hit Rate@K / Recall@K / MRR / failure analysis
```

More detail is available in [docs/architecture.md](docs/architecture.md).

## Tech stack

| Area | Technology |
| --- | --- |
| Language | Python 3.12 |
| API | FastAPI, Pydantic |
| RAG components | LangChain Core / Community |
| Vector search | FAISS |
| Local semantic embeddings | Sentence Transformers, `all-MiniLM-L6-v2` |
| Test embeddings | Deterministic local hash embeddings |
| Optional embeddings | OpenAI |
| Generation | Context-only fallback, OpenAI, or Ollama |
| Frontend | Streamlit |
| Testing | pytest |
| Code quality | Ruff |
| CI | GitHub Actions |
| Configuration | Pydantic Settings, environment variables |

The validated portfolio path uses local MiniLM embeddings and does not require a paid embedding API.

## Knowledge base

The searchable corpus currently contains synthetic support material covering:

- HTTP 503 and service availability;
- database timeout and connection issues;
- authentication failures;
- slow API responses;
- network connectivity and DNS failures;
- troubleshooting, escalation, and validation guidance.

Only these directories are loaded into the searchable corpus:

```text
data/incidents/
data/runbooks/
data/faq/
```

The benchmark lives separately under `data/evaluation/` and is not ingested into FAISS. This separation was added after identifying evaluation-data leakage during testing.

The current local index contains **25 chunks**.

## Project structure

```text
app/
  api/              FastAPI application, routes, schemas and dependencies
  core/             configuration, exceptions and structured logging
  evaluation/       metrics and retrieval evaluation runner
  ingestion/        document loaders and chunking pipeline
  rag/              embeddings, FAISS, retrieval, context and generation

data/
  incidents/        synthetic incident records
  runbooks/         troubleshooting runbooks
  faq/              support FAQ
  evaluation/       isolated benchmark dataset

reports/
  retrieval_metrics_hash.json
  retrieval_metrics_minilm.json

scripts/
  build_index.py
  run_evaluation.py
  test_local_retrieval.py

tests/              automated test suite
docs/               architecture, evaluation and limitations
.github/workflows/  CI configuration
```

## RAG workflow

For a normal query, the application follows this flow:

```text
Question
  -> retrieve Top-K chunks
  -> preserve source metadata
  -> check evidence sufficiency
  -> build traceable context
  -> generate/extract a grounded response
  -> return answer + citations/sources + timing information
```

The generation layer is provider-independent. A deterministic context-only generator can be used for local testing, while OpenAI and Ollama are optional generation providers.

## Retrieval evaluation

Retrieval is evaluated independently from generation so that retrieval failures can be measured directly.

The benchmark currently contains:

- **30 total queries**
- **25 answerable queries**
- **5 unsupported queries**
- **Top-K = 5**

Run the deterministic baseline:

```bash
python scripts/run_evaluation.py --embedding hash
```

Run the local semantic evaluation:

```bash
python scripts/run_evaluation.py --embedding minilm
```

Results are stored separately:

```text
reports/retrieval_metrics_hash.json
reports/retrieval_metrics_minilm.json
```

### Measured benchmark

The deterministic hash implementation provides a reproducible offline baseline:

```text
Hit Rate@5 : 0.92
Recall@5   : 0.92
MRR        : 0.6013
Failures   : 2
```

Using local MiniLM semantic embeddings on the same benchmark:

```text
Hit Rate@5 : 1.00
Recall@5   : 1.00
MRR        : 0.9200
Failures   : 0
```

The semantic model therefore improved both Top-5 coverage and ranking quality on the current curated dataset. Because this is a small portfolio benchmark over synthetic data, the result should not be interpreted as production-scale performance.

See [docs/evaluation.md](docs/evaluation.md) for the evaluation design.

## Local validation completed

The current checkpoint has been validated locally with:

```text
Ruff                     PASS
pytest                    18 passed
Retrieval smoke test      PASS
Indexed chunks            25
MiniLM Hit Rate@5         100%
MiniLM Recall@5           100%
MiniLM MRR                0.92
MiniLM retrieval failures 0
```

The remaining Starlette TestClient deprecation warning originates from the installed dependency stack and does not currently cause a test failure.

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/Anjalisingh127/ai-rag-knowledge-assistant.git
cd ai-rag-knowledge-assistant
```

### 2. Create the Python environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

For development and automated tests:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

For the validated local MiniLM embedding path:

```bash
pip install -e ".[dev,local]"
```

### 4. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Secrets are read from environment configuration. The local `.env` file is ignored by Git.

## Build the FAISS index

```bash
python scripts/build_index.py
```

The current MiniLM build produces a local FAISS index from 25 knowledge chunks. Generated vector-store files are intentionally excluded from version control.

## Run the quality checks

```bash
python -m ruff check .
python -m pytest
python scripts/test_local_retrieval.py
```

The automated suite currently contains **18 passing tests**.

## FastAPI application

The API layer is implemented with the following endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | service health |
| POST | `/api/retrieve` | retrieve relevant knowledge chunks |
| POST | `/api/query` | execute the RAG query workflow |
| GET | `/api/sources` | inspect available knowledge sources |
| POST | `/api/evaluate` | run retrieval evaluation |

Start it locally with:

```bash
uvicorn app.api.app:app --reload
```

OpenAPI documentation is then available at `/docs`.

**Current status:** API code and automated API tests are implemented. Full manual end-to-end validation against the real MiniLM index is the next application milestone.

## Streamlit interface

The Streamlit client is implemented and configured to communicate with the FastAPI service.

After starting the API, run:

```bash
streamlit run app/streamlit_app.py
```

**Current status:** the UI implementation exists, but final end-to-end UI validation, presentation cleanup, and portfolio screenshots are still pending.

## Provider configuration

Embedding providers:

- `local` — Sentence Transformers / MiniLM;
- `openai` — optional OpenAI embeddings.

Generation providers:

- `context` — deterministic extractive fallback suitable for free local demos and tests;
- `openai` — optional hosted generation;
- `ollama` — optional local generation.

The architecture keeps embedding and generation choices separate so that either layer can be changed without rewriting the full application.

## Testing and CI

The test suite covers the project foundation, ingestion, retrieval, generation, evaluation, and API behavior.

GitHub Actions is configured to run Ruff and pytest on pushes and pull requests to `main`. CI intentionally uses the deterministic embedding implementation rather than downloading the transformer model, keeping automated checks lightweight and independent of an external model download.

## Engineering decisions

**Evaluation isolation.** The evaluation dataset is excluded from ingestion. This prevents benchmark questions from becoming searchable evidence and artificially improving retrieval scores.

**Measured retrieval.** Hit Rate@K, Recall@K, and MRR are reported instead of an undefined “RAG accuracy” percentage.

**Local-first design.** The primary retrieval path can run locally with Sentence Transformers and FAISS without a paid API.

**Deterministic CI.** Tests use lightweight deterministic embeddings where semantic model quality is not the behavior under test.

**Source traceability.** Retrieved chunks retain metadata so responses can expose the evidence used by the RAG pipeline.

**Provider separation.** Retrieval and generation providers are configurable instead of being tightly coupled to one vendor.

## Current limitations

This is a portfolio-scale application rather than a production support platform.

Current limitations include:

- synthetic rather than production incident data;
- a small curated evaluation dataset;
- local FAISS rather than a distributed vector database;
- character-based chunking rather than a token-aware strategy;
- no BM25/hybrid retrieval or reranking layer;
- no authentication or authorization layer;
- no live ServiceNow/ticketing-system integration;
- no Docker image yet;
- no public deployment yet;
- final API/UI manual validation and demo screenshots are pending.

These limitations are intentionally documented rather than hidden. Additional detail is available in [docs/limitations.md](docs/limitations.md).

## Completed milestones

- [x] project configuration and environment structure
- [x] synthetic technical-support knowledge base
- [x] multi-format ingestion foundation
- [x] chunking and source metadata
- [x] FAISS vector retrieval
- [x] deterministic offline embedding implementation
- [x] local Sentence Transformer embedding implementation
- [x] grounded context/generation layer
- [x] retrieval sufficiency and unsupported-query handling
- [x] FastAPI service implementation
- [x] Streamlit client implementation
- [x] retrieval evaluation framework
- [x] evaluation-data isolation
- [x] hash-vs-MiniLM controlled benchmark
- [x] 18-test automated suite
- [x] Ruff quality gate
- [x] GitHub Actions workflow
- [x] benchmark reports committed to the repository

## Remaining roadmap

The next work is focused on validating and packaging the existing system rather than adding features without evidence.

1. **End-to-end API validation** — run FastAPI against the real MiniLM FAISS index and manually validate health, retrieval, query, sources, evaluation, grounding, and unsupported-query behavior.
2. **Streamlit integration validation** — run the UI against the API, test real support queries, and improve presentation where necessary.
3. **Documentation evidence** — capture representative API/UI screenshots and update the documentation with the validated workflow.
4. **Containerization** — add Docker configuration only after the local application path is stable.
5. **Deployment** — select a suitable free/low-cost deployment path for the API/UI and validate it.
6. **Final portfolio cleanup** — review README, architecture/evaluation docs, repository structure, CI status, and recruiter-facing presentation.
7. **Resume evidence** — use only the final measured metrics and completed functionality in project bullets.

Potential future improvements after the validated portfolio version include a larger evaluation set, hybrid retrieval/reranking if metrics justify it, and integration with a real support/ticketing data source.

## Documentation

- [Architecture](docs/architecture.md)
- [Evaluation methodology](docs/evaluation.md)
- [Known limitations](docs/limitations.md)

## License

MIT.
