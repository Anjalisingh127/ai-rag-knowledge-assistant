# Evaluation methodology

Retrieval and answer generation are treated as separate concerns.

The curated dataset contains 30 questions. Twenty-five are answerable from the
project knowledge base and five intentionally cover unsupported topics to test
insufficient-context behaviour.

## Retrieval metrics

- **Hit Rate@K**: whether at least one expected source appears in the top K.
- **Recall@K**: fraction of expected sources present in the top K.
- **MRR**: reciprocal rank of the first expected source.

Run:

```bash
python scripts/run_evaluation.py
```

The script writes `reports/retrieval_metrics.json`. Results are intentionally
not hard-coded into this document; benchmark values should only be published
after they are measured on the current repository state.

## Failure analysis

Missed questions are recorded with the expected and retrieved source lists.
This makes retrieval regressions visible instead of hiding them behind one
aggregate score.
