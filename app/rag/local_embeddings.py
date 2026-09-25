import hashlib
import math
import re

from langchain_core.embeddings import Embeddings


class LocalHashEmbeddings(Embeddings):
    """Deterministic local embeddings for offline development and tests.

    This lightweight provider intentionally avoids external API calls. It is
    useful for reproducible smoke tests and local portfolio demos; semantic
    quality is lower than a transformer embedding model.
    """

    def __init__(self, dimensions: int = 1024) -> None:
        if dimensions < 128:
            raise ValueError("dimensions must be at least 128")
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9_\-]+", text.lower())

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude:
            return [value / magnitude for value in vector]
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)
