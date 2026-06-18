import time
import threading
import logging
from functools import wraps

from flask import request, jsonify, current_app, g

logger = logging.getLogger(__name__)


class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def allow(self):
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate,
            )
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class RateLimiter:
    def __init__(self):
        self._buckets = {}
        self._lock = threading.Lock()

    def _get_key(self, scope, identifier):
        return f"{scope}:{identifier}"

    def _get_bucket(self, key, capacity, refill_rate):
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(capacity, refill_rate)
            return self._buckets[key]

    def limit(self, scope="global", capacity=100, refill_rate=10):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if not current_app.config.get("RATE_LIMIT_ENABLED", True):
                    return f(*args, **kwargs)

                if scope == "ip":
                    identifier = request.remote_addr or "unknown"
                elif scope == "user":
                    identifier = getattr(g, "user_id", "anonymous")
                else:
                    identifier = "global"

                key = self._get_key(scope, identifier)
                bucket = self._get_bucket(key, capacity, refill_rate)

                if not bucket.allow():
                    logger.warning("Rate limit exceeded for %s:%s", scope, identifier)
                    return jsonify(
                        {
                            "status": "error",
                            "message": "Too many requests",
                        }
                    ), 429

                return f(*args, **kwargs)

            return wrapper

        return decorator


rate_limiter = RateLimiter()
