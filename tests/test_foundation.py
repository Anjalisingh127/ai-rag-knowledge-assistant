import pytest
from pydantic import ValidationError

from app.api.schemas import QueryRequest
from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.local_embeddings import LocalHashEmbeddings


def test_question_normalizes_whitespace():
    request = QueryRequest(
        question="  How   do I resolve HTTP 503?  "
    )
    assert request.question == "How do I resolve HTTP 503?"


def test_blank_question_is_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(question="   ")


def test_chunks_preserve_source_metadata():
    chunks = prepare_knowledge_base()

    assert chunks
    assert all(chunk.metadata.get("source") for chunk in chunks)
    assert all(chunk.metadata.get("chunk_id") for chunk in chunks)
    assert any(
        chunk.metadata["source"] == "incidents/incidents.json"
        for chunk in chunks
    )


def test_local_hash_embeddings_are_deterministic():
    embeddings = LocalHashEmbeddings()
    text = "HTTP 503 database timeout"

    assert embeddings.embed_query(text) == embeddings.embed_query(text)
    assert len(embeddings.embed_query(text)) == 1024
