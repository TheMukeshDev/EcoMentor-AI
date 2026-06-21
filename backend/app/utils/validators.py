"""Pydantic-based request body validation decorator for Flask routes."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

from flask import request, jsonify
from pydantic import ValidationError as PydanticValidationError

__all__ = ["validate_body"]

logger = logging.getLogger(__name__)


def validate_body(schema_cls: type) -> Callable:
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            data = request.get_json(silent=True) or {}
            try:
                validated = schema_cls.model_validate(data)
                request.validated_body = validated.model_dump()
            except PydanticValidationError as exc:
                errors = [
                    {
                        "field": ".".join(str(p) for p in err["loc"]),
                        "message": err["msg"],
                    }
                    for err in exc.errors()
                ]
                return jsonify(
                    {
                        "status": "error",
                        "message": "Validation failed",
                        "errors": errors,
                    }
                ), 422
            return f(*args, **kwargs)

        return wrapper

    return decorator
