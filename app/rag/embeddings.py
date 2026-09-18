from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError


def get_embeddings() -> OpenAIEmbeddings:
    """Create the configured OpenAI embeddings client."""

    settings = get_settings()

    if not settings.has_openai_key or settings.openai_api_key is None:
        raise ConfigurationError(
            message="OPENAI_API_KEY is required to create embeddings."
        )

    return OpenAIEmbeddings(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_embedding_model,
        request_timeout=settings.request_timeout_seconds,
        max_retries=2,
    )