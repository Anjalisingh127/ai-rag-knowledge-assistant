import json
from datetime import UTC, datetime
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import get_settings
from app.core.exceptions import VectorStoreError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def build_vector_store(
    documents: list[Document],
    embeddings: Embeddings,
    output_directory: Path | None = None,
) -> FAISS:
    """Create and persist a FAISS vector index."""

    if not documents:
        raise VectorStoreError(
            message="Cannot create a vector store without document chunks."
        )

    settings = get_settings()
    resolved_directory = output_directory or settings.vector_store_directory
    resolved_directory.mkdir(parents=True, exist_ok=True)

    try:
        vector_store = FAISS.from_documents(documents, embeddings)
        vector_store.save_local(str(resolved_directory))

        model_name = (
            settings.local_embedding_model
            if settings.embedding_provider == "local"
            else settings.openai_embedding_model
        )
        manifest = {
            "created_at": datetime.now(UTC).isoformat(),
            "chunk_count": len(documents),
            "embedding_provider": settings.embedding_provider,
            "embedding_model": model_name,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "index_type": "FAISS",
        }

        (resolved_directory / "manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        logger.info(
            "Persisted FAISS index containing %s chunks.",
            len(documents),
        )
        return vector_store

    except Exception as error:
        logger.exception("Failed to create the FAISS vector index.")
        raise VectorStoreError(details={"reason": str(error)}) from error


def load_vector_store(
    embeddings: Embeddings,
    input_directory: Path | None = None,
) -> FAISS:
    """Load the locally generated and trusted FAISS index."""

    settings = get_settings()
    resolved_directory = input_directory or settings.vector_store_directory

    index_file = resolved_directory / "index.faiss"
    metadata_file = resolved_directory / "index.pkl"

    if not index_file.exists() or not metadata_file.exists():
        raise VectorStoreError(
            message="The FAISS index has not been built.",
            details={"directory": str(resolved_directory)},
        )

    try:
        return FAISS.load_local(
            str(resolved_directory),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception as error:
        logger.exception("Failed to load the FAISS vector index.")
        raise VectorStoreError(details={"reason": str(error)}) from error
