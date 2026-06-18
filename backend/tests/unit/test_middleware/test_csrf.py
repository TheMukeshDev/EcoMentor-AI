import time
import pytest


class TestCSRF:
    def test_generate_token_returns_four_parts(self, app_ctx):
        from app.middleware.csrf import generate_csrf_token

        token = generate_csrf_token()
        parts = token.split(":")
        assert len(parts) == 4

    def test_validate_valid_token(self, app_ctx):
        from app.middleware.csrf import generate_csrf_token, validate_csrf_token

        token = generate_csrf_token()
        assert validate_csrf_token(token, "test-secret-key") is True

    def test_validate_expired_token(self):
        from app.middleware.csrf import validate_csrf_token
        import hmac

        old_timestamp = str(int(time.time()) - 7200)
        raw = f"nonce:{old_timestamp}:"
        sig = hmac.new(b"test-secret-key", raw.encode(), "sha256").hexdigest()
        expired_token = f"nonce:{old_timestamp}::{sig}"
        assert validate_csrf_token(expired_token, "test-secret-key") is False

    def test_validate_wrong_secret(self, app_ctx):
        from app.middleware.csrf import generate_csrf_token, validate_csrf_token

        token = generate_csrf_token()
        assert validate_csrf_token(token, "wrong-secret") is False

    def test_validate_malformed_token(self):
        from app.middleware.csrf import validate_csrf_token

        assert validate_csrf_token("invalid", "secret") is False
        assert validate_csrf_token("a:b", "secret") is False
        assert validate_csrf_token("a:b:c:d:e", "secret") is False
        assert validate_csrf_token("", "secret") is False
