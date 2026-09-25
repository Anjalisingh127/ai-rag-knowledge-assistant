import json
from dataclasses import asdict
from pathlib import Path

from langchain_community.vectorstores import FAISS

from app.core.config import get_settings
from app.evaluation.metrics import (
    aggregate_retrieval_metrics,
    evaluate_retrieval_case,
)
from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.local_embeddings import LocalHashEmbeddings
from app.rag.retriever import VectorRetriever, unique_sources


def load_evaluation_dataset(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_retrieval_evaluation(top_k: int = 5) -> dict:
    settings = get_settings()
    dataset_path = settings.data_directory / "evaluation" / "rag_eval_dataset.json"
    cases = load_evaluation_dataset(dataset_path)

    chunks = prepare_knowledge_base()
    store = FAISS.from_documents(chunks, LocalHashEmbeddings())
    retriever = VectorRetriever(store)

    metric_rows = []
    failures = []
    answerable_count = 0

    for case in cases:
        if not case["answerable"]:
            continue

        answerable_count += 1
        results = retriever.retrieve(case["question"], top_k=top_k)
        sources = unique_sources(results)
        row = evaluate_retrieval_case(case["expected_sources"], sources)
        metric_rows.append(row)

        if row[0] == 0.0:
            failures.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "expected_sources": case["expected_sources"],
                    "retrieved_sources": sources,
                    "failure_type": "retrieval_failure",
                }
            )

    metrics = aggregate_retrieval_metrics(metric_rows)
    return {
        "evaluation_cases": len(cases),
        "answerable_cases": answerable_count,
        "top_k": top_k,
        **asdict(metrics),
        "failures": failures,
    }


def write_evaluation_report(result: dict) -> Path:
    settings = get_settings()
    settings.reports_directory.mkdir(parents=True, exist_ok=True)
    output = settings.reports_directory / "retrieval_metrics.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output
