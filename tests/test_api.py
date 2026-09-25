from fastapi.testclient import TestClient
from langchain_community.vectorstores import FAISS

from app.api.app import app
from app.api.dependencies import get_rag_service
from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.generation import ContextGenerator
from app.rag.local_embeddings import LocalHashEmbeddings
from app.rag.retriever import VectorRetriever
from app.rag.service import RAGService


def _test_service() -> RAGService:
    chunks = prepare_knowledge_base()
    store = FAISS.from_documents(chunks, LocalHashEmbeddings())
    return RAGService(VectorRetriever(store), ContextGenerator())


app.dependency_overrides[get_rag_service] = _test_service
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"healthy", "degraded"}


def test_retrieve_endpoint():
    response = client.post(
        "/api/retrieve",
        json={"question": "HTTP 503 database timeout", "top_k": 3},
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 3


def test_query_endpoint_returns_sources():
    response = client.post(
        "/api/query",
        json={"question": "How do I troubleshoot HTTP 503 errors?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["grounded"] is True
    assert body["sources"]


def test_query_validation_rejects_blank_question():
    response = client.post("/api/query", json={"question": " "})
    assert response.status_code == 422
