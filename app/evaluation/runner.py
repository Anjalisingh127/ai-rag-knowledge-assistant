import json
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from langchain_community.vectorstores import FAISS

from app.core.config import get_settings
from app.evaluation.metrics import (
    aggregate_retrieval_metrics,
    evaluate_retrieval_case,
)
from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.local_embeddings import LocalHashEmbeddings
from app.rag.retriever import VectorRetriever, unique_sources
from app.rag.sentence_transformer_embeddings import (
    SentenceTransformerEmbeddings,
)

EmbeddingStrategy = Literal["hash", "minilm"]


def load_evaluation_dataset(path: Path) -> list[dict]:
    """Load the curated retrieval evaluation dataset."""

    return json.loads(path.read_text(encoding="utf-8"))


def _create_embeddings(strategy: EmbeddingStrategy):
    """Create the embedding implementation used for an evaluation run."""

    if strategy == "hash":
        return LocalHashEmbeddings()

    if strategy == "minilm":
        settings = get_settings()
        return SentenceTransformerEmbeddings(
            model_name=settings.local_embedding_model
        )

    raise ValueError(f"Unsupported embedding strategy: {strategy}")


def run_retrieval_evaluation(
    top_k: int = 5,
    embedding_strategy: EmbeddingStrategy = "hash",
) -> dict:
    """Evaluate retrieval quality for one embedding strategy."""

    settings = get_settings()
    dataset_path = (
        settings.data_directory
        / "evaluation"
        / "rag_eval_dataset.json"
    )
    cases = load_evaluation_dataset(dataset_path)

    chunks = prepare_knowledge_base()
    embeddings = _create_embeddings(embedding_strategy)
    store = FAISS.from_documents(chunks, embeddings)
    retriever = VectorRetriever(store)

    metric_rows = []
    failures = []
    answerable_count = 0

    for case in cases:
        if not case["answerable"]:
            continue

        answerable_count += 1

        results = retriever.retrieve(
            case["question"],
            top_k=top_k,
        )
        sources = unique_sources(results)

        row = evaluate_retrieval_case(
            case["expected_sources"],
            sources,
        )
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
        "embedding_strategy": embedding_strategy,
        **asdict(metrics),
        "failures": failures,
    }


def write_evaluation_report(result: dict) -> Path:
    """Persist an evaluation report without overwriting another strategy."""

    settings = get_settings()
    settings.reports_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    strategy = result.get("embedding_strategy", "unknown")
    output = (
        settings.reports_directory
        / f"retrieval_metrics_{strategy}.json"
    )

    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    return output