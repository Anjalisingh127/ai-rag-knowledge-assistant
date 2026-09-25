from fastapi import APIRouter, Depends

from app.api.dependencies import get_rag_service
from app.api.schemas import (
    EvaluationResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    RetrievalItem,
    RetrieveResponse,
    SourceDocument,
    SourceReference,
)
from app.core.config import get_settings
from app.core.logging_config import create_request_id
from app.evaluation.runner import run_retrieval_evaluation
from app.ingestion.loaders import load_knowledge_base
from app.rag.service import RAGService


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    ready = (
        (settings.vector_store_directory / "index.faiss").exists()
        and (settings.vector_store_directory / "index.pkl").exists()
    )
    return HealthResponse(
        status="healthy" if ready else "degraded",
        version="0.3.0",
        vector_store_ready=ready,
        embedding_provider=settings.embedding_provider,
        llm_provider=settings.llm_provider,
    )


@router.post("/api/retrieve", response_model=RetrieveResponse)
def retrieve(
    request: QueryRequest,
    service: RAGService = Depends(get_rag_service),
) -> RetrieveResponse:
    request_id = create_request_id()
    settings = get_settings()
    results = service.retriever.retrieve(
        request.question,
        top_k=request.top_k or settings.retrieval_top_k,
        filters=request.filters,
    )
    return RetrieveResponse(
        request_id=request_id,
        results=[
            RetrievalItem(
                source=str(item.document.metadata.get("source", "unknown")),
                title=str(
                    item.document.metadata.get("title")
                    or item.document.metadata.get("file_name")
                    or item.document.metadata.get("source", "unknown")
                ),
                chunk_id=str(item.document.metadata.get("chunk_id", "unknown")),
                score=item.score,
                content=item.document.page_content,
            )
            for item in results
        ],
    )


@router.post("/api/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    request_id = create_request_id()
    settings = get_settings()
    result = service.query(
        request.question,
        top_k=request.top_k or settings.retrieval_top_k,
        filters=request.filters,
    )

    source_refs = []
    seen = set()
    for item in result.results:
        source = str(item.document.metadata.get("source", "unknown"))
        if source in seen or source not in result.sources:
            continue
        seen.add(source)
        source_refs.append(
            SourceReference(
                source=source,
                title=str(
                    item.document.metadata.get("title")
                    or item.document.metadata.get("file_name")
                    or source
                ),
                document_type=item.document.metadata.get("document_type"),
                score=item.score,
            )
        )

    return QueryResponse(
        request_id=request_id,
        answer=result.answer,
        sources=source_refs,
        grounded=result.grounded,
        retrieval_ms=result.retrieval_ms,
        generation_ms=result.generation_ms,
        total_ms=result.total_ms,
        provider=settings.llm_provider,
    )


@router.get("/api/sources", response_model=list[SourceDocument])
def sources() -> list[SourceDocument]:
    settings = get_settings()
    documents = load_knowledge_base(settings.data_directory)
    seen = set()
    response = []

    for document in documents:
        source = str(document.metadata.get("source", "unknown"))
        if source in seen:
            continue
        seen.add(source)
        response.append(
            SourceDocument(
                source=source,
                title=str(
                    document.metadata.get("title")
                    or document.metadata.get("file_name")
                    or source
                ),
                document_type=document.metadata.get("document_type"),
                category=document.metadata.get("category"),
            )
        )
    return response


@router.post("/api/evaluate", response_model=EvaluationResponse)
def evaluate() -> EvaluationResponse:
    result = run_retrieval_evaluation(top_k=5)
    return EvaluationResponse(
        evaluation_cases=result["evaluation_cases"],
        answerable_cases=result["answerable_cases"],
        top_k=result["top_k"],
        hit_rate_at_k=result["hit_rate_at_k"],
        recall_at_k=result["recall_at_k"],
        mrr=result["mrr"],
        failures=len(result["failures"]),
    )
