from app.rag.retriever import RetrievedChunk


def build_context(results: list[RetrievedChunk]) -> str:
    """Build traceable context blocks for generation."""

    blocks: list[str] = []

    for index, result in enumerate(results, start=1):
        metadata = result.document.metadata
        source = metadata.get("source", "unknown")
        title = metadata.get("title") or metadata.get("file_name") or source
        chunk_id = metadata.get("chunk_id", "unknown")

        blocks.append(
            "\n".join(
                [
                    f"[SOURCE {index}]",
                    f"title: {title}",
                    f"source: {source}",
                    f"chunk_id: {chunk_id}",
                    f"content:\n{result.document.page_content}",
                ]
            )
        )

    return "\n\n".join(blocks)
