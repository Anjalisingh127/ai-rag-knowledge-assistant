from app.core.logging_config import (
    configure_logging,
    create_request_id,
    get_logger,
)
from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.embeddings import get_embeddings
from app.rag.vector_store import build_vector_store


logger = get_logger(__name__)


def main() -> None:
    configure_logging()
    create_request_id()

    logger.info("Starting knowledge-index build.")

    chunks = prepare_knowledge_base()
    embeddings = get_embeddings()
    build_vector_store(chunks, embeddings)

    logger.info("Knowledge-index build completed successfully.")
    print(f"Indexed {len(chunks)} chunks successfully.")


if __name__ == "__main__":
    main()