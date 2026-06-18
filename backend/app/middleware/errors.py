"""Enhanced error handler middleware.

Catches all unhandled exceptions, logs full tracebacks server-side,
and returns safe generic messages with request_id to clients.
Never exposes internal paths, line numbers, or library names.
"""

from __future__ import annotations

import logging
import traceback
import uuid
from typing import Any

from flask import Flask, jsonify, request

from app.utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register all error handlers on the Flask app.

    Args:
        app: The Flask application instance.
    """
    app.register_error_handler(AppError, _handle_app_error)
    app.register_error_handler(400, _handle_bad_request)
    app.register_error_handler(404, _handle_not_found)
    app.register_error_handler(405, _handle_method_not_allowed)
    app.register_error_handler(429, _handle_too_many_requests)
    app.register_error_handler(500, _handle_internal_error)
    app.register_error_handler(Exception, _handle_unhandled)


def _generate_request_id() -> str:
    """Generate a unique request identifier.

    Returns:
        A short UUID string for tracking errors.
    """
    return uuid.uuid4().hex[:12]


def _error_response(
    message: str,
    status_code: int,
    code: str | None = None,
) -> tuple[Any, int]:
    """Build a standardized error response with request_id.

    Args:
        message: Safe user-facing error message.
        status_code: HTTP status code.
        code: Optional error code (e.g. AUTH_001).

    Returns:
        Tuple of (JSON response, status_code).
    """
    request_id = _generate_request_id()
    body: dict[str, Any] = {
        "status": "error",
        "message": message,
        "request_id": request_id,
    }
    if code:
        body["code"] = code
    return jsonify(body), status_code


def _handle_app_error(error: AppError) -> tuple[Any, int]:
    """Handle known application errors.

    Args:
        error: The AppError instance.

    Returns:
        Standardized error response.
    """
    return _error_response(error.message, error.status_code)


def _handle_bad_request(error: Exception) -> tuple[Any, int]:
    """Handle 400 Bad Request errors.

    Args:
        error: The exception.

    Returns:
        Standardized 400 response.
    """
    return _error_response("Bad request", 400)


def _handle_not_found(error: Exception) -> tuple[Any, int]:
    """Handle 404 Not Found errors.

    Args:
        error: The exception.

    Returns:
        Standardized 404 response.
    """
    return _error_response("Resource not found", 404)


def _handle_method_not_allowed(error: Exception) -> tuple[Any, int]:
    """Handle 405 Method Not Allowed errors.

    Args:
        error: The exception.

    Returns:
        Standardized 405 response.
    """
    return _error_response("Method not allowed", 405)


def _handle_too_many_requests(error: Exception) -> tuple[Any, int]:
    """Handle 429 Too Many Requests errors.

    Args:
        error: The exception.

    Returns:
        Standardized 429 response.
    """
    return _error_response("Too many requests", 429, code="RATE_001")


def _handle_internal_error(error: Exception) -> tuple[Any, int]:
    """Handle 500 Internal Server errors.

    Args:
        error: The exception.

    Returns:
        Standardized 500 response with server-side logging.
    """
    request_id = _generate_request_id()
    logger.error(
        "Internal error [%s] %s %s: %s\n%s",
        request_id,
        request.method,
        request.path,
        str(error),
        traceback.format_exc(),
    )
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "request_id": request_id,
    }), 500


def _handle_unhandled(error: Exception) -> tuple[Any, int]:
    """Catch-all handler for unhandled exceptions.

    Logs the full traceback server-side but returns only a generic
    message and request_id to the client.

    Args:
        error: The unhandled exception.

    Returns:
        Standardized 500 response.
    """
    request_id = _generate_request_id()
    logger.error(
        "Unhandled exception [%s] %s %s: %s\n%s",
        request_id,
        request.method,
        request.path,
        type(error).__name__,
        traceback.format_exc(),
    )
    return jsonify({
        "status": "error",
        "message": "An unexpected error occurred",
        "request_id": request_id,
    }), 500
