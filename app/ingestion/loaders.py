import csv
import json
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.core.exceptions import DocumentProcessingError
from app.core.logging_config import get_logger


logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".pdf"}


def _base_metadata(file_path: Path, data_root: Path) -> dict[str, Any]:
    """Create common source metadata for every loaded document."""

    try:
        relative_source = file_path.relative_to(data_root).as_posix()
    except ValueError:
        relative_source = file_path.name

    return {
        "source": relative_source,
        "file_name": file_path.name,
        "file_type": file_path.suffix.lower().lstrip("."),
    }


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract simple YAML-style metadata from a Markdown document."""

    if not content.startswith("---"):
        return {}, content

    sections = content.split("---", maxsplit=2)

    if len(sections) != 3:
        return {}, content

    metadata: dict[str, Any] = {}

    for line in sections[1].splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", maxsplit=1)
        key = key.strip()
        value = value.strip()

        if key and value:
            if key == "tags":
                metadata[key] = [
                    tag.strip() for tag in value.split(",") if tag.strip()
                ]
            else:
                metadata[key] = value

    return metadata, sections[2].strip()


def _load_markdown_or_text(
    file_path: Path,
    data_root: Path,
) -> list[Document]:
    content = file_path.read_text(encoding="utf-8-sig")
    metadata = _base_metadata(file_path, data_root)

    if file_path.suffix.lower() == ".md":
        frontmatter, content = _parse_frontmatter(content)
        metadata.update(frontmatter)

    if not content.strip():
        return []

    return [Document(page_content=content.strip(), metadata=metadata)]


def _load_json(file_path: Path, data_root: Path) -> list[Document]:
    with file_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    records = data if isinstance(data, list) else [data]
    documents: list[Document] = []

    for index, record in enumerate(records):
        metadata = _base_metadata(file_path, data_root)
        metadata["record_index"] = index

        if isinstance(record, dict):
            for metadata_key in (
                "incident_id",
                "title",
                "service",
                "environment",
                "severity",
                "status",
                "document_type",
            ):
                if metadata_key in record:
                    metadata[metadata_key] = record[metadata_key]

        page_content = json.dumps(
            record,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        documents.append(
            Document(page_content=page_content, metadata=metadata)
        )

    return documents


def _load_csv(file_path: Path, data_root: Path) -> list[Document]:
    documents: list[Document] = []

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for index, row in enumerate(reader):
            metadata = _base_metadata(file_path, data_root)
            metadata["record_index"] = index

            content_lines = [
                f"{key}: {value}"
                for key, value in row.items()
                if value is not None and value.strip()
            ]

            if content_lines:
                documents.append(
                    Document(
                        page_content="\n".join(content_lines),
                        metadata=metadata,
                    )
                )

    return documents


def _load_pdf(file_path: Path, data_root: Path) -> list[Document]:
    loaded_pages = PyPDFLoader(str(file_path)).load()
    base_metadata = _base_metadata(file_path, data_root)

    for page_number, document in enumerate(loaded_pages, start=1):
        document.metadata.update(base_metadata)
        document.metadata["page_number"] = page_number

    return loaded_pages


def load_document(
    file_path: Path,
    data_root: Path,
) -> list[Document]:
    """Load one supported knowledge-base file."""

    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return []

    try:
        if extension in {".md", ".txt"}:
            return _load_markdown_or_text(file_path, data_root)

        if extension == ".json":
            return _load_json(file_path, data_root)

        if extension == ".csv":
            return _load_csv(file_path, data_root)

        if extension == ".pdf":
            return _load_pdf(file_path, data_root)

    except Exception as error:
        logger.exception(
            "Failed to process knowledge document: %s",
            file_path,
        )
        raise DocumentProcessingError(
            details={
                "source": str(file_path),
                "reason": str(error),
            }
        ) from error

    return []


def load_knowledge_base(data_directory: Path) -> list[Document]:
    """Recursively load every supported file from the data directory."""

    if not data_directory.exists():
        raise DocumentProcessingError(
            message="The configured data directory does not exist.",
            details={"data_directory": str(data_directory)},
        )

    documents: list[Document] = []

    for file_path in sorted(data_directory.rglob("*")):
        if not file_path.is_file():
            continue

        documents.extend(load_document(file_path, data_directory))

    logger.info(
        "Knowledge base loaded with %s document records.",
        len(documents),
    )

    return documents