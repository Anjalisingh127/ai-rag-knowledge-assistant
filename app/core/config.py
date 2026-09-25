from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI-Enabled RAG Knowledge Assistant"
    app_env: str = "development"
    log_level: str = "INFO"

    embedding_provider: Literal["local", "openai"] = "local"
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_api_key: SecretStr | None = None
    openai_chat_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    llm_provider: Literal["context", "openai", "ollama"] = "context"

    chunk_size: int = Field(default=600, ge=200, le=4000)
    chunk_overlap: int = Field(default=80, ge=0, le=1000)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    max_query_length: int = Field(default=1000, ge=10, le=5000)
    request_timeout_seconds: int = Field(default=30, ge=5, le=120)

    data_directory: Path = PROJECT_ROOT / "data"
    vector_store_directory: Path = PROJECT_ROOT / "vector_store"
    logs_directory: Path = PROJECT_ROOT / "logs"
    reports_directory: Path = PROJECT_ROOT / "reports"

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
        if self.embedding_provider == "openai" and not self.has_openai_key:
            raise ValueError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai."
            )
        return self

    @property
    def has_openai_key(self) -> bool:
        return bool(
            self.openai_api_key
            and self.openai_api_key.get_secret_value().strip()
        )


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance per application process."""

    return Settings()
