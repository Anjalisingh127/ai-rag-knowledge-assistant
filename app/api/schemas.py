from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Validated request accepted by retrieval and query endpoints."""

    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Technical-support question submitted by the user.",
    )
    top_k: int | None = Field(default=None, ge=1, le=20)
    filters: dict[str, str] = Field(default_factory=dict)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 3:
            raise ValueError("Question must contain at least three characters.")
        return normalized


class SourceReference(BaseModel):
    source: str
    title: str
    document_type: str | None = None
    score: float | None = None


class RetrievalItem(BaseModel):
    source: str
    title: str
    chunk_id: str
    score: float
    content: str


class RetrieveResponse(BaseModel):
    request_id: str
    results: list[RetrievalItem]


class QueryResponse(BaseModel):
    request_id: str
    answer: str
    sources: list[SourceReference] = Field(default_factory=list)
    grounded: bool
    retrieval_ms: float = Field(ge=0)
    generation_ms: float = Field(ge=0)
    total_ms: float = Field(ge=0)
    provider: str


class EvaluationResponse(BaseModel):
    evaluation_cases: int
    answerable_cases: int
    top_k: int
    hit_rate_at_k: float
    recall_at_k: float
    mrr: float
    failures: int


class SourceDocument(BaseModel):
    source: str
    title: str
    document_type: str | None = None
    category: str | None = None


class ErrorResponse(BaseModel):
    request_id: str
    error_code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    vector_store_ready: bool
    embedding_provider: str
    llm_provider: str
