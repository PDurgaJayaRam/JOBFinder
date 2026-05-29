"""Structured logging configuration for the AI Career Agent."""

import os
import logging
import json
from datetime import datetime
from typing import Optional
from collections import deque


# In-memory log buffer for the /api/v1/logs endpoint (last 500 entries)
_log_buffer = deque(maxlen=500)


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry)


class BufferHandler(logging.Handler):
    """Captures log records into an in-memory buffer."""

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            _log_buffer.append({
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "raw": msg,
            })
        except Exception:
            pass


def setup_logging(log_level: str = "INFO"):
    """Configure structured logging for the application."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler with structured format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # Buffer handler for API-accessible logs
    buffer_handler = BufferHandler()
    buffer_handler.setLevel(level)
    buffer_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(buffer_handler)

    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return root_logger


def get_recent_logs(limit: int = 100, level: Optional[str] = None):
    """Retrieve recent log entries from the buffer."""
    logs = list(_log_buffer)
    if level:
        level_upper = level.upper()
        logs = [l for l in logs if l.get("level") == level_upper]
    return logs[-limit:]
