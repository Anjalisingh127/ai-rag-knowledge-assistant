from dataclasses import dataclass
from typing import Iterable

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


@dataclass(frozen=True)
class RetrievedChunk:
    document: Document
    score: float


def _matches_filters(document: Document, filters: dict[str, str]) -> bool:
    if not filters:
        return True

    for key, expected in filters.items():
        actual = document.metadata.get(key)
        if actual is None:
            return False
        if str(actual).lower() != expected.lower():
            return False
    return True


class VectorRetriever:
    """Small retrieval service that preserves scores and source metadata."""

    def __init__(self, vector_store: FAISS) -> None:
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: dict[str, str] | None = None,
        candidate_multiplier: int = 4,
    ) -> list[RetrievedChunk]:
        normalized_query = " ".join(query.split())
        if not normalized_query:
            return []

        candidate_k = max(top_k, top_k * candidate_multiplier)
        results = self.vector_store.similarity_search_with_score(
            normalized_query,
            k=candidate_k,
        )

        selected: list[RetrievedChunk] = []
        for document, score in results:
            if _matches_filters(document, filters or {}):
                selected.append(
                    RetrievedChunk(document=document, score=float(score))
                )
            if len(selected) >= top_k:
                break

        return selected


def unique_sources(results: Iterable[RetrievedChunk]) -> list[str]:
    seen: set[str] = set()
    sources: list[str] = []

    for result in results:
        source = str(result.document.metadata.get("source", "unknown"))
        if source not in seen:
            seen.add(source)
            sources.append(source)

    return sources
