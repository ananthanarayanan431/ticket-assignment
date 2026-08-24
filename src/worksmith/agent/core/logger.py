"""
Structured logging for the agent graph — every node and edge logs through
this instead of print(), so log lines are one-JSON-object-per-line with the
fields (ticket_id, node, decision, etc.) queryable rather than baked into a
free-text message.

Separate from `core.log._log`: that module persists the durable audit trail
to Postgres; this one is for operational/observability logging (stdout).
"""

import json
import logging
import os
import sys
from typing import Any


class _StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            **getattr(record, "fields", {}),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_ROOT_NAME = "worksmith"


def _configure_root() -> None:
    root = logging.getLogger(_ROOT_NAME)
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_StructuredFormatter())
    root.addHandler(handler)
    root.setLevel(os.environ.get("WORKSMITH_LOG_LEVEL", "INFO").upper())
    root.propagate = False


class StructLogger:
    """Thin wrapper so call sites pass fields as kwargs instead of building `extra` dicts."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _emit(self, level: int, event: str, exc_info: bool, fields: dict[str, Any]) -> None:
        self._logger.log(level, event, extra={"fields": fields}, exc_info=exc_info)

    def debug(self, event: str, **fields: Any) -> None:
        self._emit(logging.DEBUG, event, False, fields)

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, False, fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._emit(logging.WARNING, event, False, fields)

    def error(self, event: str, *, exc_info: bool = False, **fields: Any) -> None:
        self._emit(logging.ERROR, event, exc_info, fields)


def get_logger(name: str) -> StructLogger:
    _configure_root()
    return StructLogger(logging.getLogger(f"{_ROOT_NAME}.{name}"))
