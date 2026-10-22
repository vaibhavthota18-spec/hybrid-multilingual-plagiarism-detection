"""
Structured JSON Logging with Request Correlation and Sensitive Field Redaction
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

REDACTED_KEYS = {"password", "token", "secret", "authorization", "hashed_password", "jwt_secret"}


class JSONLogFormatter(logging.Formatter):
    """
    Formats log records into machine-readable JSON lines with privacy filters.
    """
    def __init__(self, service_name: str = "plagiarism-backend"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": self.service_name,
            "message": record.getMessage(),
        }

        # Include request_id correlation if present on record
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Redact any extra dictionary attributes that match sensitive names
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            clean_extra = {}
            for k, v in record.extra.items():
                if any(red in k.lower() for red in REDACTED_KEYS):
                    clean_extra[k] = "[REDACTED]"
                else:
                    clean_extra[k] = v
            log_obj["data"] = clean_extra

        return json.dumps(log_obj)


def setup_logging(level: str = "INFO", service_name: str = "plagiarism-backend") -> None:
    """Configures root logger with JSONLogFormatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter(service_name=service_name))
    root_logger.addHandler(handler)

    # Quiet overly chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
