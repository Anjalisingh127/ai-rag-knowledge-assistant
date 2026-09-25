import re
import time
from dataclasses import dataclass

from app.rag.context import build_context
from app.rag.generation import Generator
from app.rag.retriever import RetrievedChunk, VectorRetriever, unique_sources

_STOPWORDS = {
    "what", "when", "where", "which", "with", "from", "that", "this",
    "should", "could", "would", "about", "after", "before", "into",
    "have", "does", "your", "their", "there", "how", "the", "and",
}


@dataclass(frozen=True)
class QueryResult:
    answer: str
    sources: list[str]
    grounded: bool
    retrieval_ms: float
    generation_ms: float
    total_ms: float
    results: list[RetrievedChunk]


def _has_relevant_context(question: str, results: list[RetrievedChunk]) -> bool:
    terms = {
        token
        for token in re.findall(r"[a-z0-9_\-]+", question.lower())
        if len(token) > 2 and token not in _STOPWORDS
    }
    if not terms or not results:
        return False

    context = " ".join(
        result.document.page_content.lower() for result in results
    )
    return any(term in context for term in terms)


class RAGService:
    def __init__(self, retriever: VectorRetriever, generator: Generator) -> None:
        self.retriever = retriever
        self.generator = generator

    def query(
        self,
        question: str,
        *,
        top_k: int = 5,
        filters: dict[str, str] | None = None,
    ) -> QueryResult:
        total_start = time.perf_counter()

        retrieval_start = time.perf_counter()
        results = self.retriever.retrieve(
            question,
            top_k=top_k,
            filters=filters,
        )
        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

        if not _has_relevant_context(question, results):
            total_ms = (time.perf_counter() - total_start) * 1000
            return QueryResult(
                answer=(
                    "I couldn't find sufficient information in the available "
                    "knowledge base to answer this reliably."
                ),
                sources=[],
                grounded=False,
                retrieval_ms=retrieval_ms,
                generation_ms=0.0,
                total_ms=total_ms,
                results=results,
            )

        context = build_context(results)
        generation_start = time.perf_counter()
        answer = self.generator.generate(question, context)
        generation_ms = (time.perf_counter() - generation_start) * 1000
        total_ms = (time.perf_counter() - total_start) * 1000

        return QueryResult(
            answer=answer,
            sources=unique_sources(results),
            grounded=True,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            total_ms=total_ms,
            results=results,
        )
