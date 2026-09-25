import contextvars
import json
import logging
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="system",
)


class JsonFormatter(logging.Formatter):
    """Format application logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": _request_id.get(),
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging() -> None:
    """Configure structured logging for the application."""

    settings = get_settings()
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    if root_logger.handlers:
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named application logger."""

    return logging.getLogger(name)


def create_request_id() -> str:
    """Create and activate a unique request identifier."""

    request_id = str(uuid.uuid4())
    _request_id.set(request_id)
    return request_id


def set_request_id(request_id: str) -> None:
    """Set a request identifier supplied by another application layer."""

    _request_id.set(request_id)


def get_request_id() -> str:
    """Return the active request identifier."""

    return _request_id.get()
