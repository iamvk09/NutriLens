"""
NutriLens Structured Logging Module
Provides standardized logging with timestamp, log level, module context, and request IDs.
"""

import logging
import sys
import json
import uuid
from datetime import datetime
from typing import Any, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import settings


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging in production."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logger(name: str = "nutrilens") -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        if settings.ENVIRONMENT.lower() == "production":
            handler.setFormatter(JsonFormatter())
        else:
            standard_format = (
                "[%(asctime)s] [%(levelname)s] [%(name)s:%(module)s:%(lineno)d] %(message)s"
            )
            handler.setFormatter(logging.Formatter(standard_format, datefmt="%Y-%m-%d %H:%M:%S"))

        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger("nutrilens")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request method, path, status, and duration with unique request-id."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = datetime.utcnow()
        try:
            response = await call_next(request)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.1f}ms)",
                extra={"request_id": request_id}
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                f"Unhandled error handling {request.method} {request.url.path}: {str(exc)} ({duration_ms:.1f}ms)",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise exc
