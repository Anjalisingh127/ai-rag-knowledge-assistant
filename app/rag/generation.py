import re
from abc import ABC, abstractmethod

import httpx
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, GenerationError
from app.rag.prompts import SYSTEM_PROMPT


class Generator(ABC):
    @abstractmethod
    def generate(self, question: str, context: str) -> str:
        raise NotImplementedError


class ContextGenerator(Generator):
    """Deterministic extractive fallback for free local demos and tests."""

    def generate(self, question: str, context: str) -> str:
        if not context.strip():
            return (
                "I couldn't find sufficient information in the available "
                "knowledge base to answer this reliably."
            )

        query_terms = {
            term
            for term in re.findall(r"[a-z0-9_\-]+", question.lower())
            if len(term) > 3
        }
        sentences = re.split(r"(?<=[.!?])\s+|\n+", context)
        ranked = []
        for sentence in sentences:
            clean = sentence.strip()
            if not clean or clean.startswith(
                ("[SOURCE", "title:", "source:", "chunk_id:", "content:")
            ):
                continue
            score = sum(term in clean.lower() for term in query_terms)
            if score:
                ranked.append((score, clean))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = []
        for _, sentence in ranked:
            if sentence not in selected:
                selected.append(sentence)
            if len(selected) == 4:
                break

        if not selected:
            return (
                "I couldn't find sufficient information in the available "
                "knowledge base to answer this reliably."
            )

        return " ".join(selected)


class OpenAIGenerator(Generator):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.has_openai_key or settings.openai_api_key is None:
            raise ConfigurationError(
                message="OPENAI_API_KEY is required for OpenAI generation."
            )
        self._model = ChatOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_chat_model,
            temperature=0,
            timeout=settings.request_timeout_seconds,
            max_retries=2,
        )

    def generate(self, question: str, context: str) -> str:
        response = self._model.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("human", f"CONTEXT\n{context}\n\nQUESTION\n{question}"),
            ]
        )
        return str(response.content).strip()


class OllamaGenerator(Generator):
    def generate(self, question: str, context: str) -> str:
        settings = get_settings()
        try:
            response = httpx.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": (
                        f"{SYSTEM_PROMPT}\n\nCONTEXT\n{context}"
                        f"\n\nQUESTION\n{question}\n\nANSWER"
                    ),
                    "stream": False,
                    "options": {"temperature": 0},
                },
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            return str(response.json().get("response", "")).strip()
        except Exception as error:
            raise GenerationError(
                message="Local Ollama generation failed.",
                details={"reason": str(error)},
            ) from error


def get_generator() -> Generator:
    provider = get_settings().llm_provider
    if provider == "openai":
        return OpenAIGenerator()
    if provider == "ollama":
        return OllamaGenerator()
    return ContextGenerator()
