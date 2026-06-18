import time
import threading
import pytest


class TestTokenBucket:
    def test_allow_returns_true_when_tokens_available(self):
        from app.utils.rate_limiter import TokenBucket

        bucket = TokenBucket(10, 1)
        for _ in range(10):
            assert bucket.allow() is True

    def test_denies_when_empty(self):
        from app.utils.rate_limiter import TokenBucket

        bucket = TokenBucket(1, 1)
        assert bucket.allow() is True
        assert bucket.allow() is False

    def test_refills_over_time(self):
        from app.utils.rate_limiter import TokenBucket

        bucket = TokenBucket(1, 10)
        assert bucket.allow() is True
        assert bucket.allow() is False
        time.sleep(0.2)
        assert bucket.allow() is True

    def test_does_not_exceed_capacity(self):
        from app.utils.rate_limiter import TokenBucket

        bucket = TokenBucket(5, 100)
        time.sleep(0.2)
        for _ in range(5):
            assert bucket.allow() is True
        assert bucket.allow() is False


class TestRateLimiter:
    def test_limit_decorator_allows_request(self, app_ctx, mocker):
        from app.utils.rate_limiter import rate_limiter

        mock_fn = mocker.MagicMock(return_value="ok")
        decorated = rate_limiter.limit(scope="global", capacity=100, refill_rate=10)(
            mock_fn
        )
        result = decorated()
        assert result == "ok"

    def test_limit_returns_429_when_exceeded(self, app_ctx, mocker):
        from app.utils.rate_limiter import rate_limiter

        mocker.patch.object(rate_limiter, "_buckets", {})
        mock_fn = mocker.MagicMock()
        decorated = rate_limiter.limit(scope="global", capacity=0, refill_rate=0)(
            mock_fn
        )
        result = decorated()
        assert result[0].json["status"] == "error"
        assert result[1] == 429
