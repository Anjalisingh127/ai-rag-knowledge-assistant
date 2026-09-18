from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Validated request accepted by the RAG query endpoint."""

    query: str = Field(
        min_length=3,
        max_length=1000,
        description="Support question submitted by the user.",
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Optional number of relevant chunks to retrieve.",
    )
    filters: dict[str, str] = Field(
        default_factory=dict,
        description="Optional metadata filters.",
    )

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = " ".join(value.split())

        if len(normalized) < 3:
            raise ValueError("Query must contain at least three characters.")

        return normalized


class SourceReference(BaseModel):
    """Source metadata returned with a grounded answer."""

    source: str
    document_type: str
    title: str
    section: str | None = None
    score: float | None = Field(default=None, ge=0.0)


class QueryResponse(BaseModel):
    """Structured response returned by the RAG workflow."""

    request_id: str
    answer: str
    sources: list[SourceReference] = Field(default_factory=list)
    grounded: bool
    latency_ms: float = Field(ge=0)
    model: str


class ErrorResponse(BaseModel):
    """Safe error information returned to API consumers."""

    request_id: str
    error_code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Application health and dependency status."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    vector_store_ready: bool
    openai_configured: bool
    