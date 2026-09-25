from functools import lru_cache

from app.rag.embeddings import get_embeddings
from app.rag.generation import get_generator
from app.rag.retriever import VectorRetriever
from app.rag.service import RAGService
from app.rag.vector_store import load_vector_store


@lru_cache
def get_rag_service() -> RAGService:
    embeddings = get_embeddings()
    vector_store = load_vector_store(embeddings)
    return RAGService(
        retriever=VectorRetriever(vector_store),
        generator=get_generator(),
    )
