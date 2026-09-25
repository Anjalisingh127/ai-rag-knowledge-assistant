from pathlib import Path

from app.ingestion.loaders import load_document
from app.ingestion.pipeline import prepare_knowledge_base


def test_expanded_knowledge_base_loads_multiple_categories():
    chunks = prepare_knowledge_base()
    sources = {chunk.metadata["source"] for chunk in chunks}

    assert "runbooks/http_503_service_unavailable.md" in sources
    assert "runbooks/database_timeout.md" in sources
    assert "runbooks/authentication_failure.md" in sources
    assert "runbooks/slow_api_response.md" in sources
    assert "runbooks/network_connectivity.md" in sources
    assert "faq/support_faq.md" in sources


def test_markdown_frontmatter_becomes_metadata():
    data_root = Path("data")
    documents = load_document(
        data_root / "runbooks" / "database_timeout.md",
        data_root,
    )

    assert documents
    assert documents[0].metadata["document_type"] == "runbook"
    assert documents[0].metadata["category"] == "database"
