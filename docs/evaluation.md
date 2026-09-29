# Evaluation Methodology

Retrieval and answer generation are evaluated as separate concerns so retrieval quality can be measured directly rather than inferred from generated text.

The curated benchmark contains **30 questions**:

- **25 answerable support queries**
- **5 intentionally unsupported queries**
- **Top-K = 5**

The unsupported questions verify that the application can distinguish between in-domain knowledge and questions that are not supported by the current corpus.

## Retrieval Metrics

The project reports three retrieval metrics:

- **Hit Rate@K** — whether at least one expected source appears within the top K retrieved results.
- **Recall@K** — the fraction of expected relevant sources recovered within the top K results.
- **Mean Reciprocal Rank (MRR)** — the reciprocal rank of the first expected source, which rewards retrieving the right source earlier.

These metrics describe **retrieval quality**, not end-to-end RAG accuracy.

## Evaluation Isolation

Evaluation data is stored under:

```text
data/evaluation/
```

The ingestion pipeline only indexes the support knowledge directories:

```text
data/incidents/
data/runbooks/
data/faq/
```

Keeping the benchmark outside the searchable corpus prevents evaluation questions from becoming retrievable evidence and avoids benchmark leakage.

## Running the Evaluation

Run the deterministic hash baseline:

```bash
python scripts/run_evaluation.py --embedding hash
```

Run the local semantic MiniLM evaluation:

```bash
python scripts/run_evaluation.py --embedding minilm
```

The reports are stored separately:

```text
reports/retrieval_metrics_hash.json
reports/retrieval_metrics_minilm.json
```

## Current Measured Results

| Retrieval strategy | Hit Rate@5 | Recall@5 | MRR | Answerable retrieval failures |
| --- | ---: | ---: | ---: | ---: |
| Deterministic hash baseline | 0.92 | 0.92 | 0.6013 | 2 |
| MiniLM semantic embeddings | **1.00** | **1.00** | **0.9200** | **0** |

The MiniLM evaluation uses `sentence-transformers/all-MiniLM-L6-v2` with FAISS on the same corpus and query set used for the deterministic baseline.

Because the benchmark is small, curated, and based on synthetic support data, these results should be interpreted as portfolio-scale evidence rather than production-scale performance.

## Failure Analysis

For answerable queries, the evaluation runner records a retrieval failure when none of the expected sources appears in the Top-K result set.

Each failure record includes:

- query ID;
- question text;
- expected source list;
- retrieved source list;
- failure type.

This makes regressions visible at the individual-query level instead of hiding them behind aggregate metrics.

## CI Strategy

The default evaluation strategy remains the deterministic hash implementation so automated tests can run without downloading the optional Sentence Transformers dependency.

MiniLM is imported only when the semantic evaluation strategy is requested. This keeps GitHub Actions lightweight while preserving a locally validated semantic benchmark.

## Related Files

- [Evaluation runner](../app/evaluation/runner.py)
- [Evaluation dataset](../data/evaluation/rag_eval_dataset.json)
- [Hash baseline report](../reports/retrieval_metrics_hash.json)
- [MiniLM semantic report](../reports/retrieval_metrics_minilm.json)
- [Project README](../README.md)
