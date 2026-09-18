from functools import lru_cache
from pathlib import Path

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

    app_name: str = "Enterprise Support RAG Knowledge Assistant"
    app_env: str = "development"
    log_level: str = "INFO"

    openai_api_key: SecretStr | None = None
    openai_chat_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    chunk_size: int = Field(default=800, ge=200, le=4000)
    chunk_overlap: int = Field(default=120, ge=0, le=1000)
    retrieval_top_k: int = Field(default=4, ge=1, le=20)
    max_query_length: int = Field(default=1000, ge=10, le=5000)
    request_timeout_seconds: int = Field(default=30, ge=5, le=120)

    data_directory: Path = PROJECT_ROOT / "data"
    vector_store_directory: Path = PROJECT_ROOT / "vector_store"
    logs_directory: Path = PROJECT_ROOT / "logs"

    @model_validator(mode="after")
    def validate_chunk_configuration(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
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