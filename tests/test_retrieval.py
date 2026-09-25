from langchain_community.vectorstores import FAISS

from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.local_embeddings import LocalHashEmbeddings
from app.rag.retriever import VectorRetriever, unique_sources


def _build_retriever() -> VectorRetriever:
    chunks = prepare_knowledge_base()
    store = FAISS.from_documents(chunks, LocalHashEmbeddings())
    return VectorRetriever(store)


def test_http_503_query_returns_relevant_source():
    retriever = _build_retriever()

    results = retriever.retrieve(
        "HTTP 503 service unavailable and database timeout",
        top_k=5,
    )

    sources = unique_sources(results)
    assert any("http_503" in source for source in sources)
    assert any(
        "503" in result.document.page_content
        for result in results
    )


def test_metadata_filter_limits_results():
    retriever = _build_retriever()

    results = retriever.retrieve(
        "database timeout payment service",
        top_k=5,
        filters={"category": "database"},
    )

    assert results
    assert all(
        str(result.document.metadata.get("category", "")).lower() == "database"
        for result in results
    )


def test_blank_query_returns_no_results():
    retriever = _build_retriever()
    assert retriever.retrieve("   ") == []
