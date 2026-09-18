import hashlib
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.exceptions import DocumentProcessingError
from app.core.logging_config import get_logger
from app.ingestion.loaders import load_knowledge_base


logger = get_logger(__name__)


def _create_chunk_id(source: str, chunk_index: int, content: str) -> str:
    """Create a stable identifier for a document chunk."""

    identifier = f"{source}:{chunk_index}:{content}".encode("utf-8")
    return hashlib.sha256(identifier).hexdigest()[:16]


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Split documents while preserving and extending source metadata."""

    settings = get_settings()
    resolved_chunk_size = chunk_size or settings.chunk_size
    resolved_chunk_overlap = (
        settings.chunk_overlap
        if chunk_overlap is None
        else chunk_overlap
    )

    if resolved_chunk_overlap >= resolved_chunk_size:
        raise DocumentProcessingError(
            message="Chunk overlap must be smaller than chunk size.",
            details={
                "chunk_size": resolved_chunk_size,
                "chunk_overlap": resolved_chunk_overlap,
            },
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=resolved_chunk_size,
        chunk_overlap=resolved_chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks: list[Document] = []

    for document_index, document in enumerate(documents):
        split_documents = splitter.split_documents([document])

        for chunk_index, chunk in enumerate(split_documents):
            source = str(chunk.metadata.get("source", "unknown"))

            chunk.metadata.update(
                {
                    "document_index": document_index,
                    "chunk_index": chunk_index,
                    "chunk_id": _create_chunk_id(
                        source,
                        chunk_index,
                        chunk.page_content,
                    ),
                }
            )

            chunks.append(chunk)

    logger.info(
        "Created %s chunks from %s document records.",
        len(chunks),
        len(documents),
    )

    return chunks


def prepare_knowledge_base(
    data_directory: Path | None = None,
) -> list[Document]:
    """Load and chunk the complete knowledge base."""

    settings = get_settings()
    resolved_directory = data_directory or settings.data_directory

    documents = load_knowledge_base(resolved_directory)

    if not documents:
        raise DocumentProcessingError(
            message="No supported knowledge documents were found.",
            details={"data_directory": str(resolved_directory)},
        )

    return chunk_documents(documents)