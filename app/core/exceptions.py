from typing import Any


class ApplicationError(Exception):
    """Base exception for errors that can be safely handled by the API."""

    error_code = "APPLICATION_ERROR"
    status_code = 500
    default_message = "An unexpected application error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(ApplicationError):
    error_code = "CONFIGURATION_ERROR"
    status_code = 500
    default_message = "The application is not configured correctly."


class DocumentProcessingError(ApplicationError):
    error_code = "DOCUMENT_PROCESSING_ERROR"
    status_code = 422
    default_message = "The knowledge document could not be processed."


class VectorStoreError(ApplicationError):
    error_code = "VECTOR_STORE_ERROR"
    status_code = 503
    default_message = "The knowledge index is currently unavailable."


class RetrievalError(ApplicationError):
    error_code = "RETRIEVAL_ERROR"
    status_code = 503
    default_message = "Relevant support information could not be retrieved."


class GenerationError(ApplicationError):
    error_code = "GENERATION_ERROR"
    status_code = 502
    default_message = "A grounded response could not be generated."


class UnsupportedQueryError(ApplicationError):
    error_code = "UNSUPPORTED_QUERY"
    status_code = 422
    default_message = "The query cannot be answered from the available knowledge base."