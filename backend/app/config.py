import os
from dotenv import load_dotenv

load_dotenv()


def _parse_rate_limit(value, default):
    parts = value.split(";")
    if len(parts) == 2:
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return default
    return default


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ecomentor-dev")
    FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")

    JSON_SORT_KEYS = False
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    RATE_LIMIT_DEFAULT = _parse_rate_limit(
        os.getenv("RATE_LIMIT_DEFAULT", "100;3600"), (100, 3600)
    )
    RATE_LIMIT_STRICT = _parse_rate_limit(
        os.getenv("RATE_LIMIT_STRICT", "10;60"), (10, 60)
    )


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    CORS_ORIGINS = ["http://localhost:5000", "http://localhost:8080"]


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    FIRESTORE_EMULATOR_HOST = "localhost:8080"
    CORS_ORIGINS = ["*"]


class ProductionConfig(BaseConfig):
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
