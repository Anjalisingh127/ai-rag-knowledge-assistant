from app.evaluation.metrics import (
    aggregate_retrieval_metrics,
    evaluate_retrieval_case,
)
from app.evaluation.runner import load_evaluation_dataset
from app.core.config import get_settings


def test_retrieval_metric_math():
    row = evaluate_retrieval_case(
        ["runbooks/a.md", "runbooks/b.md"],
        ["runbooks/x.md", "runbooks/a.md"],
    )

    assert row == (1.0, 0.5, 0.5)


def test_metric_aggregation():
    metrics = aggregate_retrieval_metrics(
        [(1.0, 1.0, 1.0), (0.0, 0.0, 0.0)]
    )

    assert metrics.hit_rate_at_k == 0.5
    assert metrics.recall_at_k == 0.5
    assert metrics.mrr == 0.5


def test_evaluation_dataset_has_answerable_and_abstention_cases():
    settings = get_settings()
    cases = load_evaluation_dataset(
        settings.data_directory / "evaluation" / "rag_eval_dataset.json"
    )

    assert len(cases) == 30
    assert any(case["answerable"] for case in cases)
    assert any(not case["answerable"] for case in cases)
