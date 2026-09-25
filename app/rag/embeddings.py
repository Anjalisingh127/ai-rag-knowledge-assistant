from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError
from app.rag.sentence_transformer_embeddings import (
    SentenceTransformerEmbeddings,
)


def get_embeddings() -> Embeddings:
    """Create the configured embedding provider."""

    settings = get_settings()

    if settings.embedding_provider == "local":
        return SentenceTransformerEmbeddings(settings.local_embedding_model)

    if not settings.has_openai_key or settings.openai_api_key is None:
        raise ConfigurationError(
            message="OPENAI_API_KEY is required for OpenAI embeddings."
        )

    return OpenAIEmbeddings(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_embedding_model,
        request_timeout=settings.request_timeout_seconds,
        max_retries=2,
    )
