"""Custom exception classes for structured API error handling."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AppError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
]


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, status_code=422)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, status_code=403)
