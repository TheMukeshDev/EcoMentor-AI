import time
import pytest
import json


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

    def test_validate_token_with_user_id(self, app_ctx):
        from app.middleware.csrf import generate_csrf_token, validate_csrf_token

        token = generate_csrf_token("user-123")
        assert validate_csrf_token(token, "test-secret-key", "user-123") is True
        assert validate_csrf_token(token, "test-secret-key", "wrong-user") is False

    def test_csrf_protect_skips_get(self, app_ctx):
        from flask import Flask
        from app.middleware.csrf import csrf_protect

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test"
        app.config["TESTING"] = False

        @app.route("/test", methods=["GET"])
        @csrf_protect
        def view():
            return "ok"

        with app.test_client() as client:
            resp = client.get("/test")
            assert resp.status_code == 200

    def test_csrf_protect_requires_token_on_post(self):
        from flask import Flask
        from app.middleware.csrf import csrf_protect

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"
        app.config["TESTING"] = False

        @app.route("/test", methods=["POST"])
        @csrf_protect
        def view():
            return "ok"

        with app.test_client() as client:
            resp = client.post("/test", json={})
            assert resp.status_code == 403
            data = resp.get_json()
            assert "CSRF" in data["message"]

    def test_csrf_protect_invalid_token_returns_403(self):
        from flask import Flask
        from app.middleware.csrf import csrf_protect

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"
        app.config["TESTING"] = False

        @app.route("/test", methods=["POST"])
        @csrf_protect
        def view():
            return "ok"

        with app.test_client() as client:
            resp = client.post(
                "/test",
                json={},
                headers={"X-CSRF-Token": "bad:token:data:sig"}
            )
            assert resp.status_code == 403

    def test_csrf_protect_valid_token_passes(self):
        from flask import Flask
        from app.middleware.csrf import csrf_protect, generate_csrf_token

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["TESTING"] = False

        @app.route("/test", methods=["POST"])
        @csrf_protect
        def view():
            return "ok"

        with app.app_context():
            token = generate_csrf_token()

        with app.test_client() as client:
            resp = client.post(
                "/test",
                json={},
                headers={"X-CSRF-Token": token}
            )
            assert resp.status_code == 200

    def test_csrf_protect_bypassed_in_testing(self):
        from flask import Flask
        from app.middleware.csrf import csrf_protect

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"
        app.config["TESTING"] = True

        @app.route("/test", methods=["POST"])
        @csrf_protect
        def view():
            return "ok"

        with app.test_client() as client:
            resp = client.post("/test", json={})
            assert resp.status_code == 200

    def test_csrf_token_endpoint(self):
        from flask import Flask
        from app.middleware.csrf import csrf_token_endpoint

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret-key"
        app.add_url_rule("/csrf", "csrf", csrf_token_endpoint)

        with app.test_client() as client:
            resp = client.get("/csrf")
            assert resp.status_code == 200
            data = resp.get_json()
            assert "csrf_token" in data
            parts = data["csrf_token"].split(":")
            assert len(parts) == 4

