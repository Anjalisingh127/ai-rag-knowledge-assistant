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

    _METADATA_PREFIXES = (
        "[source",
        "title:",
        "source:",
        "chunk_id:",
        "content:",
    )

    _IRRELEVANT_PHRASES = (
        "synthetic",
        "last_reviewed",
        "document_id",
        "document_type",
    )

    _ACTION_PATTERN = re.compile(
        r"^(check|verify|review|confirm|determine|record|correlate|"
        r"inspect|identify|monitor|run|compare|restore|restart|"
        r"correct|scale|escalate)\b"
    )

    @staticmethod
    def _normalize_line(line: str) -> str:
        """Remove list markers while preserving knowledge-base wording."""
        return re.sub(r"^\s*(?:[-*]|\d+\.)\s*", "", line).strip()

    @classmethod
    def _is_useful_line(cls, line: str) -> bool:
        """Return True when a line contains useful answer content."""
        normalized = line.strip()

        if not normalized:
            return False

        # Ignore incomplete section-introduction lines such as
        # "Escalate when:", "Search for:", and "Request:".
        if normalized.endswith(":"):
            return False

        lowered = normalized.lower()

        # Ignore metadata inserted by build_context().
        if lowered.startswith(cls._METADATA_PREFIXES):
            return False

        # Ignore Markdown headings and YAML delimiters.
        if normalized.startswith("#") or normalized == "---":
            return False

        # Ignore standalone JSON structure.
        if normalized in {"{", "}", "[", "]", "},", "],"}:
            return False

        # Ignore raw JSON key/value fields from incident records.
        if re.match(r'^"[a-zA-Z0-9_ -]+"\s*:', normalized):
            return False

        # Ignore raw JSON string values from arrays, for example:
        # "HTTP 503 on login",
        if re.match(r'^".*"\s*,?$', normalized):
            return False

        # Ignore project/dataset metadata that does not help troubleshooting.
        if any(
            phrase in lowered
            for phrase in cls._IRRELEVANT_PHRASES
        ):
            return False

        return True

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

        candidates: list[tuple[int, int, str]] = []

        for position, line in enumerate(context.splitlines()):
            clean = self._normalize_line(line)

            if not self._is_useful_line(clean):
                continue

            lowered = clean.lower()

            # Rank lines by their overlap with the user's question.
            score = sum(term in lowered for term in query_terms)

            # Prefer operational instructions over descriptive text.
            if self._ACTION_PATTERN.match(lowered):
                score += 1

            if score > 0:
                candidates.append((score, position, clean))

        if not candidates:
            return (
                "I couldn't find sufficient information in the available "
                "knowledge base to answer this reliably."
            )

        # Rank strongest evidence first. Position resolves equal-score ties.
        candidates.sort(key=lambda item: (-item[0], item[1]))

        selected: list[tuple[int, str]] = []
        seen: set[str] = set()

        for _, position, candidate in candidates:
            normalized_candidate = candidate.lower()

            if normalized_candidate in seen:
                continue

            seen.add(normalized_candidate)
            selected.append((position, candidate))

            if len(selected) == 4:
                break

        # Restore the original source order so the answer reads coherently.
        selected.sort(key=lambda item: item[0])

        return " ".join(
            candidate
            for _, candidate in selected
        )


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
                (
                    "human",
                    f"CONTEXT\n{context}\n\nQUESTION\n{question}",
                ),
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
                    "options": {
                        "temperature": 0,
                    },
                },
                timeout=settings.request_timeout_seconds,
            )

            response.raise_for_status()

            return str(
                response.json().get("response", "")
            ).strip()

        except Exception as error:
            raise GenerationError(
                message="Local Ollama generation failed.",
                details={
                    "reason": str(error),
                },
            ) from error


def get_generator() -> Generator:
    provider = get_settings().llm_provider

    if provider == "openai":
        return OpenAIGenerator()

    if provider == "ollama":
        return OllamaGenerator()

    return ContextGenerator()