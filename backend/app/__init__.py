"""EcoMentor AI application factory.

Creates and configures the Flask application with all extensions,
blueprints, middleware, and error handlers.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from app.config import config_by_name
from app.extensions import init_firestore
from app.middleware.errors import register_error_handlers
from app.utils.secrets import validate_required_secrets
from app.middleware.csrf import csrf_token_endpoint
from app.utils.rate_limiter import rate_limiter


class JSONLogFormatter(logging.Formatter):
    """Structured JSON log formatter for production observability.

    Outputs each log record as a single-line JSON object with
    timestamp, level, logger name, and message fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON-encoded string representing the log entry.
        """
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'testing', 'production'.

    Returns:
        Configured Flask application instance.

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    if config_name is None:
        config_name = os.getenv("APP_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    _setup_logging(app)
    _setup_extensions(app, config_name)
    _register_blueprints(app)
    register_error_handlers(app)
    _register_request_hooks(app)
    _register_additional_routes(app)

    return app


def _setup_logging(app: Flask) -> None:
    """Configure structured JSON logging for the application.

    Args:
        app: The Flask application instance.
    """
    handler = logging.StreamHandler(sys.stdout)
    level = logging.DEBUG if app.debug else logging.INFO
    handler.setLevel(level)
    handler.setFormatter(JSONLogFormatter())
    app.logger.addHandler(handler)
    app.logger.setLevel(level)


def _setup_extensions(app: Flask, config_name: str) -> None:
    """Initialize Flask extensions in correct order.

    Args:
        app: The Flask application instance.
        config_name: The configuration environment name.
    """
    validate_required_secrets(app)

    CORS(app, origins=app.config.get("CORS_ORIGINS", ["*"]))

    # Flask-Talisman: security headers (skip in testing)
    if config_name != "testing":
        _setup_talisman(app, config_name)

    init_firestore(app)


def _setup_talisman(app: Flask, config_name: str) -> None:
    """Configure Flask-Talisman for security headers.

    Args:
        app: The Flask application instance.
        config_name: The configuration environment name.
    """
    try:
        from flask_talisman import Talisman

        csp = {
            "default-src": "'self'",
            "script-src": "'self' https://www.gstatic.com",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src": "'self' https://fonts.gstatic.com",
            "img-src": "'self' data:",
            "connect-src": (
                "'self' "
                "https://identitytoolkit.googleapis.com "
                "https://securetoken.googleapis.com"
            ),
        }

        force_https = config_name == "production"

        Talisman(
            app,
            content_security_policy=csp,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            strict_transport_security_include_subdomains=True,
            force_https=force_https,
            session_cookie_secure=force_https,
        )
    except ImportError:
        app.logger.warning("flask-talisman not installed, skipping")


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints with the application.

    Args:
        app: The Flask application instance.
    """
    blueprints: list[tuple[str, str]] = [
        ("auth", "/api/auth"),
        ("dashboard", "/api/dashboard"),
        ("activities", "/api/activities"),
        ("ai", "/api/ai"),
        ("leaderboard", "/api/leaderboard"),
    ]

    for name, prefix in blueprints:
        module = __import__(
            f"app.blueprints.{name}.routes", fromlist=["routes"]
        )
        blueprint = getattr(module, f"{name}_bp")
        app.register_blueprint(blueprint, url_prefix=prefix)


def _register_request_hooks(app: Flask) -> None:
    """Register before/after request hooks.

    Args:
        app: The Flask application instance.
    """

    @app.before_request
    def apply_global_rate_limit() -> Any:
        """Enforce global rate limiting on all requests."""
        capacity = app.config.get("RATE_LIMIT_GLOBAL_CAPACITY", 1000)
        refill = app.config.get("RATE_LIMIT_GLOBAL_REFILL", 10)
        bucket = rate_limiter._get_bucket("global:all", capacity, refill)
        if not bucket.allow():
            return jsonify({
                "status": "error",
                "message": "Too many requests",
            }), 429

    @app.before_request
    def log_request() -> None:
        """Log incoming requests at DEBUG level."""
        app.logger.debug("%s %s", request.method, request.path)

    @app.after_request
    def add_security_headers(response: Any) -> Any:
        """Add security headers to every response.

        Args:
            response: The Flask response object.

        Returns:
            Modified response with security headers.
        """
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response

    @app.teardown_appcontext
    def shutdown_session(exception: BaseException | None = None) -> None:
        """Clean up resources on app context teardown.

        Args:
            exception: Optional exception that triggered teardown.
        """
        pass


def _register_additional_routes(app: Flask) -> None:
    """Register standalone routes not tied to blueprints.

    Args:
        app: The Flask application instance.
    """
    app.add_url_rule(
        "/api/auth/csrf-token",
        "csrf_token",
        csrf_token_endpoint,
        methods=["GET"],
    )

    @app.route("/health")
    def health() -> dict[str, str]:
        """Health check endpoint for load balancers.

        Returns:
            Dict with status key.
        """
        return {"status": "healthy"}

    @app.route("/")
    def index() -> dict[str, str]:
        """Root endpoint.

        Returns:
            Dict with API status.
        """
        return {
            "status": "online",
            "message": "EcoMentor AI Backend API is running.",
        }
