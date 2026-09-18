"""No-cost retrieval smoke test; does not call the OpenAI API."""

import hashlib
import math
import re
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from app.ingestion.pipeline import prepare_knowledge_base


class LocalTestEmbeddings(Embeddings):
    """Deterministic token vectors for testing indexing and search only."""

    dimensions = 512

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude:
            vector = [value / magnitude for value in vector]

        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def main() -> None:
    chunks = prepare_knowledge_base()
    embeddings = LocalTestEmbeddings()
    index = FAISS.from_documents(chunks, embeddings)

    output_directory = Path("vector_store_mock")
    output_directory.mkdir(exist_ok=True)
    index.save_local(str(output_directory))

    query = "How do I investigate HTTP 503 database timeout errors?"
    results = index.similarity_search_with_score(query, k=3)

    print(f"Indexed chunks: {len(chunks)}")
    print(f"Query: {query}")

    for rank, (document, distance) in enumerate(results, start=1):
        print(
            f"{rank}. source={document.metadata['source']} "
            f"chunk={document.metadata['chunk_index']} "
            f"distance={distance:.4f}"
        )

    assert len(chunks) == 7, "Expected seven chunks from the current sample data."
    assert results, "Search returned no results."
    assert any(
        "503" in document.page_content or "DATABASE_TIMEOUT" in document.page_content
        for document, _ in results
    ), "Expected a relevant 503 or database-timeout chunk among the top results."

    print("Local retrieval smoke test passed. No OpenAI API call was made.")


if __name__ == "__main__":
    main()