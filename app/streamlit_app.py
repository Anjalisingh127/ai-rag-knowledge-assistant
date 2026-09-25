import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


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
        with st.spinner("Retrieving support knowledge..."):
            response = httpx.post(
                f"{API_BASE_URL}/api/query",
                json={"question": question, "top_k": 5},
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

        st.subheader("Answer")
        st.write(result["answer"])

        if result["grounded"]:
            st.success("Grounded in retrieved project knowledge")
        else:
            st.warning("Insufficient supporting context found")

        st.subheader("Sources")
        if result["sources"]:
            for source in result["sources"]:
                with st.expander(source["title"]):
                    st.code(source["source"])
                    if source.get("document_type"):
                        st.write(f"Type: {source['document_type']}")
        else:
            st.write("No supporting sources returned.")

        with st.expander("Request details"):
            st.json(
                {
                    "request_id": result["request_id"],
                    "provider": result["provider"],
                    "retrieval_ms": result["retrieval_ms"],
                    "generation_ms": result["generation_ms"],
                    "total_ms": result["total_ms"],
                }
            )
    except Exception as error:
        st.error(f"Request failed: {error}")
