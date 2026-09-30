# Limitations

- The incident, runbook and FAQ corpus is synthetic and curated for this portfolio project.
- The FAISS index is intended for a single-service portfolio deployment, not distributed production search.
- The evaluation set is intentionally small and domain-specific.
- The no-cost context generator is extractive; richer generative behaviour requires the optional OpenAI or Ollama provider.
- MiniLM requires the sentence-transformer model to be available at runtime. On a fresh local or cloud environment, model initialization and index creation can make the first request slower than later requests.
- The public Streamlit deployment runs the RAG service in-process rather than through the separate FastAPI service used locally and in Docker.
- Streamlit Community Cloud is appropriate for a portfolio demo, but instance restarts, cold starts, dependency installation and platform resource limits can affect startup time and availability.
- The public deployment does not provide production features such as autoscaling guarantees, persistent distributed vector storage, authentication, authorization, rate limiting or observability infrastructure.
- Retrieval scores from FAISS are implementation-dependent and should not be presented as calibrated confidence probabilities.
- OpenAI and Ollama integrations are configurable but are not part of the validated public benchmark path.
