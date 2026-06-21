import logging
from functools import wraps

from flask import request, jsonify
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


def validate_body(schema_cls):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
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
