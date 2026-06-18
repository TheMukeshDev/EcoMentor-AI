import logging
import sys

from flask import Flask, request, jsonify
from flask_cors import CORS

from app.config import config_by_name
from app.extensions import init_firestore
from app.utils.errors import AppError
from app.utils.secrets import validate_required_secrets
from app.middleware.csrf import csrf_token_endpoint


def create_app(config_name=None):
    if config_name is None:
        config_name = "development"

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    setup_logging(app)
    setup_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_request_hooks(app)
    register_additional_routes(app)

    return app


def setup_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)


def setup_extensions(app):
    validate_required_secrets(app)
    CORS(app, origins=app.config.get("CORS_ORIGINS", ["*"]))
    init_firestore(app)


def register_blueprints(app):
    blueprints = [
        ("auth", "/api/auth"),
        ("dashboard", "/api/dashboard"),
        ("activities", "/api/activities"),
        ("ai", "/api/ai"),
        ("leaderboard", "/api/leaderboard"),
    ]

    for name, prefix in blueprints:
        module = __import__(f"app.blueprints.{name}.routes", fromlist=["routes"])
        blueprint = getattr(module, f"{name}_bp")
        app.register_blueprint(blueprint, url_prefix=prefix)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify(
            {
                "status": "error",
                "message": error.message,
            }
        ), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify(
            {
                "status": "error",
                "message": "Resource not found",
            }
        ), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify(
            {
                "status": "error",
                "message": "Method not allowed",
            }
        ), 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        app.logger.exception("Internal server error")
        return jsonify(
            {
                "status": "error",
                "message": "Internal server error",
            }
        ), 500


def register_request_hooks(app):
    @app.before_request
    def log_request():
        app.logger.debug("%s %s", request.method, request.path)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        pass


def register_additional_routes(app):
    app.add_url_rule(
        "/api/auth/csrf-token",
        "csrf_token",
        csrf_token_endpoint,
        methods=["GET"],
    )
