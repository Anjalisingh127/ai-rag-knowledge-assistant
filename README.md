# AI-Enabled RAG Knowledge Assistant

A portfolio-scale technical-support **Retrieval-Augmented Generation (RAG)** application built to search incident records, runbooks, and FAQs, retrieve relevant evidence, and return grounded troubleshooting answers with source traceability.

The project models a practical support-engineering workflow: before suggesting an action, the system retrieves evidence from a controlled knowledge base, checks whether the retrieved context is sufficiently relevant, and either produces a grounded response or abstains when the available evidence is insufficient.

> **Project status:** Core RAG pipeline, semantic retrieval, grounding, retrieval evaluation, FastAPI API, Streamlit interface, automated tests, and local end-to-end validation are complete. Docker packaging, public deployment, and final demo assets remain in progress.

## Current results

The retrieval layer is evaluated on a curated **30-query benchmark** containing **25 answerable support questions** and **5 intentionally unsupported questions**.

| Retrieval strategy | Hit Rate@5 | Recall@5 | MRR | Answerable retrieval failures |
| --- | ---: | ---: | ---: | ---: |
| Deterministic hash baseline | 92% | 92% | 0.6013 | 2 |
| MiniLM semantic embeddings | **100%** | **100%** | **0.9200** | **0** |

Both strategies use the same knowledge corpus, evaluation questions, and Top-K value. Evaluation files are deliberately excluded from the searchable corpus to prevent benchmark leakage.

> **Important:** These are **retrieval metrics**, not a claim of "100% RAG accuracy." Hit Rate@5 and Recall@5 measure whether expected evidence is retrieved within the top five results; MRR also measures how highly the first expected source is ranked.

## Why I built it

Technical-support work often involves searching incident history and troubleshooting documentation before deciding what to investigate next. I built this project to model that workflow while learning how a RAG application can be structured, tested, measured, and exposed as a usable service.

The design focuses on:

- local/free execution for the primary portfolio workflow;
- source-aware retrieval and grounded responses;
- measurable retrieval quality rather than vague accuracy claims;
- separation between ingestion, retrieval, grounding, generation, API, and UI layers;
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
User Question -----------+
                         v
              +----------------------+
              | Vector Retriever     |
              | Top-K + metadata     |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | Grounding Check      |
              | evidence sufficiency |
              +----------+-----------+
                         |
              +----------+-----------+
              |                      |
              v                      v
       sufficient context     insufficient context
              |                      |
              v                      v
      Generation Layer            Abstain
      context/OpenAI/Ollama          |
              |                      |
              +----------+-----------+
                         |
                         v
              Answer + Sources
                         |
              +----------+-----------+
              |                      |
              v                      v
         FastAPI API            Streamlit UI
```

The evaluation pipeline remains separate from the searchable knowledge base:

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

The benchmark lives separately under `data/evaluation/` and is not ingested into FAISS. This prevents benchmark questions from becoming searchable evidence and artificially improving retrieval results.

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
  -> return answer + sources + timing information
```

The grounding check evaluates whether an individual retrieved chunk contains sufficient meaningful query-term coverage. Weakly related retrieval results therefore do not automatically become supporting evidence.

The default context generator provides deterministic extractive responses for free local demos and tests. It filters internal RAG metadata and raw JSON fields before producing user-facing output. OpenAI and Ollama remain optional generation providers.

## End-to-end validation

The local application path has been manually validated through:

```text
Streamlit
  -> FastAPI / RAG service
  -> MiniLM embeddings
  -> FAISS retrieval
  -> grounding validation
  -> context generation or abstention
  -> source attribution
```

Two important runtime behaviors were verified.

**Supported query**

```text
How should I troubleshoot HTTP 503 errors?
```

The application retrieves relevant support documentation, passes the grounding check, produces a troubleshooting response, and exposes supporting sources.

**Unsupported query**

```text
How do I fix Kubernetes pod eviction?
```

Kubernetes troubleshooting is outside the current knowledge base. The application therefore returns its insufficient-context response, marks the result as ungrounded, and does not expose unrelated retrieved documents as supporting sources.

The `/api/evaluate` application path was also validated using MiniLM semantic retrieval and returned the same measured benchmark values reported above.

## Retrieval evaluation

Retrieval is evaluated independently from generation so retrieval failures can be measured directly.

The benchmark contains:

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

Deterministic hash baseline:

```text
Hit Rate@5 : 0.92
Recall@5   : 0.92
MRR        : 0.6013
Failures   : 2
```

Local MiniLM semantic embeddings:

```text
Hit Rate@5 : 1.00
Recall@5   : 1.00
MRR        : 0.9200
Failures   : 0
```

MiniLM improved both Top-5 coverage and ranking quality on the current curated dataset. Because this is a small portfolio benchmark over synthetic data, these results should not be interpreted as production-scale performance.

See [docs/evaluation.md](docs/evaluation.md) for the evaluation design.

## Validated checkpoint

The current local checkpoint has been validated with:

```text
Ruff                         PASS
pytest                       19 passed
Retrieval smoke test         PASS
Indexed chunks               25
MiniLM Hit Rate@5            100%
MiniLM Recall@5              100%
MiniLM MRR                   0.92
MiniLM retrieval failures    0
Supported-query grounding    PASS
Unsupported-query abstention PASS
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

The automated suite currently contains **19 passing tests**.

Regression coverage verifies, among other behaviors, that:

- unsupported questions abstain instead of producing unsupported answers;
- internal RAG metadata does not leak into user-facing responses;
- raw incident JSON fields are excluded from generated answers;
- knowledge-base whitespace remains intact during ingestion and chunking.

## FastAPI application

The API layer exposes:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | service health |
| POST | `/api/retrieve` | retrieve relevant knowledge chunks |
| POST | `/api/query` | execute the grounded RAG query workflow |
| GET | `/api/sources` | inspect available knowledge sources |
| POST | `/api/evaluate` | run the MiniLM retrieval benchmark |

Start it locally with:

```bash
uvicorn app.api.app:app --reload
```

OpenAPI documentation is then available at `/docs`.

The API has been manually validated against the real local MiniLM/FAISS path, including retrieval evaluation and grounding behavior.

## Streamlit interface

The Streamlit client communicates with the FastAPI service and provides an interactive interface for support questions.

After starting the API, run:

```bash
streamlit run app/streamlit_app.py
```

The UI has been manually validated for both a supported HTTP 503 troubleshooting query and an unsupported Kubernetes query. Final portfolio screenshots remain to be added.

## Provider configuration

Embedding providers:

- `local` — Sentence Transformers / MiniLM;
- `openai` — optional OpenAI embeddings.

Generation providers:

- `context` — deterministic extractive fallback suitable for free local demos and tests;
- `openai` — optional hosted generation;
- `ollama` — optional local generation.

Embedding and generation choices are kept separate so either layer can be changed without rewriting the full application.

## Testing and CI

The test suite covers the project foundation, ingestion, retrieval, generation, grounding, evaluation, and API behavior.

GitHub Actions is configured to run Ruff and pytest on pushes and pull requests to `main`. CI intentionally uses deterministic embeddings rather than downloading the transformer model, keeping automated checks lightweight and independent of an external model download.

## Engineering decisions

**Evaluation isolation.** Evaluation data is excluded from ingestion, preventing benchmark questions from becoming searchable evidence.

**Measured retrieval.** Hit Rate@K, Recall@K, and MRR are reported instead of an undefined "RAG accuracy" percentage.

**Ground before generation.** Retrieved evidence must meet a minimum relevance threshold before generation is allowed. Unsupported queries can therefore abstain instead of presenting weak evidence as fact.

**Local-first design.** The primary retrieval path can run locally with Sentence Transformers and FAISS without a paid API.

**Deterministic CI.** Tests use lightweight deterministic embeddings where semantic model quality is not the behavior under test.

**Source traceability.** Retrieved chunks retain metadata so grounded responses can expose the evidence used by the RAG pipeline.

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
- OpenAI and Ollama generation paths are configurable but are not part of the validated local E2E benchmark;
- no Docker image yet;
- no public deployment yet;
- final portfolio screenshots are still pending.

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
- [x] 19-test automated suite
- [x] Ruff quality gate
- [x] GitHub Actions workflow
- [x] benchmark reports committed to the repository
- [x] end-to-end API validation with MiniLM/FAISS
- [x] Streamlit supported-query validation
- [x] Streamlit unsupported-query abstention validation

## Remaining roadmap

The next work is focused on packaging and presenting the validated system rather than adding features without evidence.

1. **Documentation evidence** — capture representative API/UI screenshots and add them to the project documentation.
2. **Containerization** — add Docker configuration for the validated application path.
3. **Deployment** — select a suitable free/low-cost deployment path for the API/UI and validate it.
4. **Deployment verification** — verify the public application, API health, retrieval, grounding, and unsupported-query behavior.
5. **Final portfolio cleanup** — review README, architecture/evaluation docs, repository structure, CI status, and recruiter-facing presentation.
6. **Resume evidence** — use only measured metrics and completed functionality in project bullets.

Potential future improvements after the validated portfolio version include a larger evaluation set, hybrid retrieval/reranking if metrics justify it, and integration with a real support/ticketing data source.

## Documentation

- [Architecture](docs/architecture.md)
- [Evaluation methodology](docs/evaluation.md)
- [Known limitations](docs/limitations.md)

## License

MIT.
