from pathlib import Path

import streamlit as st

from app.core.config import get_settings
from app.core.logging_config import create_request_id
from app.ingestion.pipeline import prepare_knowledge_base
from app.rag.embeddings import get_embeddings
from app.rag.generation import get_generator
from app.rag.retriever import VectorRetriever
from app.rag.service import RAGService
from app.rag.vector_store import build_vector_store, load_vector_store


@st.cache_resource(show_spinner=False)
def get_cloud_rag_service() -> RAGService:
    """Build or load the local index and return one cached RAG service."""

    settings = get_settings()
    embeddings = get_embeddings()

    index_file = Path(settings.vector_store_directory) / "index.faiss"
    metadata_file = Path(settings.vector_store_directory) / "index.pkl"

    if not index_file.exists() or not metadata_file.exists():
        chunks = prepare_knowledge_base()
        build_vector_store(chunks, embeddings)

    vector_store = load_vector_store(embeddings)

    return RAGService(
        retriever=VectorRetriever(vector_store),
        generator=get_generator(),
    )


def build_source_references(result) -> list[dict[str, str | float | None]]:
    """Convert retrieved chunks into the source cards shown by the UI."""

    references: list[dict[str, str | float | None]] = []
    seen: set[str] = set()

    for item in result.results:
        source = str(item.document.metadata.get("source", "unknown"))

        if source in seen or source not in result.sources:
            continue

        seen.add(source)
        references.append(
            {
                "source": source,
                "title": str(
                    item.document.metadata.get("title")
                    or item.document.metadata.get("file_name")
                    or source
                ),
                "document_type": item.document.metadata.get("document_type"),
                "score": item.score,
            }
        )

    return references


st.set_page_config(
    page_title="RAG Knowledge Assistant",
    page_icon="🔎",
    layout="centered",
)

st.title("AI-Enabled RAG Knowledge Assistant")
st.caption(
    "Ask questions about the synthetic incident, runbook and support FAQ "
    "knowledge base. Answers include traceable sources."
)

question = st.text_area(
    "Technical support question",
    placeholder="How should I troubleshoot repeated HTTP 503 errors?",
    height=110,
)

if st.button("Ask", type="primary", disabled=not question.strip()):
    try:
        with st.spinner("Loading and retrieving support knowledge..."):
            service = get_cloud_rag_service()
            settings = get_settings()
            request_id = create_request_id()

            result = service.query(
                question.strip(),
                top_k=settings.retrieval_top_k,
            )
            sources = build_source_references(result)

        st.subheader("Answer")
        st.write(result.answer)

        if result.grounded:
            st.success("Grounded in retrieved project knowledge")
        else:
            st.warning("Insufficient supporting context found")

        st.subheader("Sources")
        if sources:
            for source in sources:
                with st.expander(str(source["title"])):
                    st.code(str(source["source"]))
                    if source.get("document_type"):
                        st.write(f"Type: {source['document_type']}")
        else:
            st.write("No supporting sources returned.")

        with st.expander("Request details"):
            st.json(
                {
                    "request_id": request_id,
                    "provider": settings.llm_provider,
                    "retrieval_ms": result.retrieval_ms,
                    "generation_ms": result.generation_ms,
                    "total_ms": result.total_ms,
                    "execution_mode": "in-process",
                }
            )
    except Exception as error:
        st.error(f"Request failed: {error}")
