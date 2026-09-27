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

def test_http_503_runbook_preserves_text_integrity():
    """Ensure ingestion and chunking never remove meaningful whitespace."""

    chunks = prepare_knowledge_base()

    runbook_chunks = [
        chunk
        for chunk in chunks
        if chunk.metadata.get("source")
        == "runbooks/http_503_service_unavailable.md"
    ]

    assert runbook_chunks

    combined_content = "\n".join(
        chunk.page_content for chunk in runbook_chunks
    )

    expected_phrases = [
        "Use this runbook",
        "incidents and operational",
        "connection pool",
        "Initial triage",
        "deployments and configuration",
        "dependency logs",
        "Deployment checks",
        "after confirming",
        "HTTP 503 rate",
        "Affected service and environment",
    ]

    for phrase in expected_phrases:
        assert phrase in combined_content

    corrupted_phrases = [
        "thisrunbook",
        "incidentsand",
        "connectionpool",
        "Initialtriage",
        "deploymentsand",
        "dependencylogs",
        "Deploymentchecks",
        "afterconfirming",
        "HTTP503",
        "serviceand environment",
    ]

    for phrase in corrupted_phrases:
        assert phrase not in combined_content
