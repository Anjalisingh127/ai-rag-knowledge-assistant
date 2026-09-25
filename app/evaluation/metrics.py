from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    hit_rate_at_k: float
    recall_at_k: float
    mrr: float


def evaluate_retrieval_case(
    expected_sources: list[str],
    retrieved_sources: list[str],
) -> tuple[float, float, float]:
    if not expected_sources:
        return 0.0, 0.0, 0.0

    expected = set(expected_sources)
    retrieved = retrieved_sources

    hit = 1.0 if any(source in expected for source in retrieved) else 0.0
    recall = len(expected.intersection(retrieved)) / len(expected)

    reciprocal_rank = 0.0
    for rank, source in enumerate(retrieved, start=1):
        if source in expected:
            reciprocal_rank = 1.0 / rank
            break

    return hit, recall, reciprocal_rank


def aggregate_retrieval_metrics(
    rows: list[tuple[float, float, float]],
) -> RetrievalMetrics:
    if not rows:
        return RetrievalMetrics(0.0, 0.0, 0.0)

    count = len(rows)
    return RetrievalMetrics(
        hit_rate_at_k=sum(row[0] for row in rows) / count,
        recall_at_k=sum(row[1] for row in rows) / count,
        mrr=sum(row[2] for row in rows) / count,
    )
