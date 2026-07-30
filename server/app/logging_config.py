"""
Structured JSON logging.

One JSON object per line, so Render's log stream stays greppable and machine-parseable.

Secrets are never logged. This module does not receive settings and has no access to
DATABASE_URL; callers pass only credential-free fields such as the backend scheme and host.
Redaction here is a backstop, not the primary control: the primary control is that no call site
passes a secret in the first place.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from typing import Any

# Backstop redaction. Catches a connection string that reaches a log record by mistake, for
# example inside a driver exception message.
#
# The userinfo class is greedy and deliberately allows "@", so that a password containing "@"
# is consumed up to the final separator. A non-greedy or @-excluding class would stop at the
# first "@" and leave the tail of the password visible.
_CREDENTIAL_URL = re.compile(r"(?P<scheme>[a-zA-Z0-9+.\-]+://)(?P<userinfo>[^/\s]+)@")

_RESERVED = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", "levelname",
    "levelno", "lineno", "module", "msecs", "message", "msg", "name", "pathname", "process",
    "processName", "relativeCreated", "stack_info", "thread", "threadName", "taskName",
}


def redact(text: str) -> str:
    """Replace userinfo in any URL-like substring with ***."""
    return _CREDENTIAL_URL.sub(lambda m: f"{m.group('scheme')}***@", text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload[key] = redact(value) if isinstance(value, str) else value

        if record.exc_info:
            payload["exception"] = redact(self.formatException(record.exc_info))

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # uvicorn installs its own handlers; route them through the same formatter so the stream
    # stays uniformly JSON.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
