import os
import logging

"""Google Cloud Secret Manager integration with env var fallback."""

logger = logging.getLogger(__name__)

_client = None
_initialized = False


def _get_client():
    global _client
    if _client is None:
        try:
            from google.cloud import secretmanager

            _client = secretmanager.SecretManagerServiceClient()
        except Exception:
            logger.warning("Secret Manager client unavailable")
            return None
    return _client


def get_secret(name, default=None):
    project_id = os.getenv("GCP_PROJECT_ID")
    env = os.getenv("APP_ENV", "development")

    if env == "production":
        client = _get_client()
        if client:
            try:
                full_name = f"projects/{project_id}/secrets/{name}/versions/latest"
                response = client.access_secret_version(request={"name": full_name})
                return response.payload.data.decode("utf-8")
            except Exception as exc:
                logger.error("Failed to fetch secret %s: %s", name, exc)

    return os.getenv(name, default)


def validate_required_secrets(app):
    required = ["SECRET_KEY", "GEMINI_API_KEY"]
    if app.config.get("APP_ENV") == "production":
        required.append("GCP_PROJECT_ID")

    missing = []
    for key in required:
        value = get_secret(key) or app.config.get(key)
        if not value:
            missing.append(key)

    if missing:
        raise RuntimeError(f"Missing required secrets: {', '.join(missing)}")
