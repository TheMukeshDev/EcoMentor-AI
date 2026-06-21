"""Standardized JSON response helpers for consistent API output format."""

from __future__ import annotations

from typing import Any

from flask import jsonify

__all__ = ["success_response", "error_response"]


def success_response(data: Any, status_code: int = 200) -> tuple:  # noqa: ANN401
    return jsonify({"status": "success", "data": data}), status_code


def error_response(message: str, status_code: int = 400) -> tuple:
    return jsonify({"status": "error", "message": message}), status_code
