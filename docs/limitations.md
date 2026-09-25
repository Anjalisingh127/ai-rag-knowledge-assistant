# Limitations

- The incident, runbook and FAQ corpus is synthetic and curated for this
  portfolio project.
- The local FAISS index is intended for a single-service demo, not distributed
  production search.
- The evaluation set is intentionally small and domain-specific.
- The no-cost context generator is extractive; richer generative behaviour
  requires the optional OpenAI or Ollama provider.
- Local transformer embeddings require a one-time model download.
- Retrieval scores from FAISS are implementation-dependent and should not be
  presented as calibrated confidence probabilities.
