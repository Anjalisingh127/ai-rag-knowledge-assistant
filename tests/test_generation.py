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


def test_known_query_returns_clean_grounded_answer():
    result = _service().query(
        "How should I troubleshoot HTTP 503 errors?",
        top_k=5,
    )

    # The supported query must produce a grounded answer with citations.
    assert result.grounded is True
    assert result.sources
    assert "503" in result.answer or "service" in result.answer.lower()

    # Internal RAG metadata must never leak into the user-facing answer.
    assert "[SOURCE" not in result.answer
    assert "chunk_id:" not in result.answer
    assert "source:" not in result.answer
    assert "content:" not in result.answer

    # Raw JSON fields from incident records must not appear in the answer.
    assert '"title":' not in result.answer
    assert '"service":' not in result.answer
    assert '"incident_id":' not in result.answer
    assert '"root_cause":' not in result.answer

    # Raw JSON array values must not leak into the generated answer.
    assert '"HTTP 503 on login"' not in result.answer

    # Common spacing-corruption patterns must never reach the final answer.
    corrupted_phrases = [
        "thisrunbook",
        "responses.All",
        "responses. All",
        "isbelow",
        "forat",
        "anddetection",
        "alertthreshold",
        "environmentand",
        "trafficexceeded",
        "downstreamdependency",
    ]

    for phrase in corrupted_phrases:
        assert phrase not in result.answer


def test_unknown_query_abstains_without_citations():
    result = _service().query(
        "How do I fix Kubernetes pod eviction?",
        top_k=5,
    )

    # Unsupported questions must abstain instead of hallucinating an answer.
    assert result.grounded is False
    assert result.sources == []
    assert result.generation_ms == 0.0
    assert "couldn't find sufficient information" in result.answer
