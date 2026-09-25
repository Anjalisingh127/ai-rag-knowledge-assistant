from langchain_community.vectorstores import FAISS

from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.generation import ContextGenerator
from app.rag.local_embeddings import LocalHashEmbeddings
from app.rag.retriever import VectorRetriever
from app.rag.service import RAGService


def _service() -> RAGService:
    chunks = prepare_knowledge_base()
    store = FAISS.from_documents(chunks, LocalHashEmbeddings())
    return RAGService(VectorRetriever(store), ContextGenerator())


def test_known_query_returns_sources():
    result = _service().query(
        "How should I troubleshoot HTTP 503 errors?",
        top_k=5,
    )

    assert result.grounded is True
    assert result.sources
    assert "503" in result.answer or "service" in result.answer.lower()


def test_unknown_query_abstains_without_citations():
    result = _service().query(
        "How do I fix Kubernetes pod eviction?",
        top_k=5,
    )

    assert result.grounded is False
    assert result.sources == []
    assert "couldn't find sufficient information" in result.answer
