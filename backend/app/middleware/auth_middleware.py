from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import request, g

from app.utils.errors import AuthenticationError


"""Firebase ID token verification middleware for Flask routes.

Provides the `require_auth` decorator that validates Bearer tokens
and injects the authenticated user identity into the request context.
"""

__all__ = ["require_auth"]


def require_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that verifies a Firebase Bearer ID token and populates ``g``."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid Authorization header")
        id_token = auth_header.split(" ", 1)[1]
        from firebase_admin import auth as firebase_auth

        try:
            decoded = firebase_auth.verify_id_token(id_token)
            g.current_user = decoded
            g.user_id = decoded["uid"]
        except Exception as exc:
            raise AuthenticationError(f"Invalid token: {exc}")
        return f(*args, **kwargs)

    return decorated
