import pytest


class TestCacheService:
    def test_get_miss_returns_none(self):
        from app.services.cache_service import CacheService

        cache = CacheService()
        result = cache.get("user-1", "recommendations")
        assert result is None

    def test_set_and_get(self):
        from app.services.cache_service import CacheService

        cache = CacheService()
        cache.set("user-1", "recommendations", {"tip": "test"})
        result = cache.get("user-1", "recommendations")
        assert result == {"tip": "test"}

    def test_get_from_local_cache(self):
        from app.services.cache_service import CacheService

        cache = CacheService()
        cache.set("user-1", "recommendations", {"tip": "test"})
        result1 = cache.get("user-1", "recommendations")
        result2 = cache.get("user-1", "recommendations")
        assert result1 == result2

    def test_invalidate_specific(self):
        from app.services.cache_service import CacheService

        cache = CacheService()
        cache.set("user-1", "recommendations", {"tip": "test"})
        cache.set("user-1", "daily_mission", {"challenge": "do something"})
        cache.invalidate("user-1", "recommendations")
        assert cache.get("user-1", "recommendations") is None
        assert cache.get("user-1", "daily_mission") is not None

    def test_invalidate_all(self):
        from app.services.cache_service import CacheService

        cache = CacheService()
        cache.set("user-1", "recommendations", {"tip": "test"})
        cache.set("user-1", "daily_mission", {"challenge": "do something"})
        cache.invalidate("user-1")
        assert cache.get("user-1", "recommendations") is None
        assert cache.get("user-1", "daily_mission") is None

    def test_clear(self):
        from app.services.cache_service import CacheService

        cache = CacheService()
        cache.set("user-1", "recommendations", {"tip": "test"})
        cache.clear()
        assert cache.get("user-1", "recommendations") is None

    def test_enforces_limit(self):
        from app.services.cache_service import CacheService, MAX_LOCAL_ENTRIES

        cache = CacheService()
        for i in range(MAX_LOCAL_ENTRIES + 100):
            cache.set(f"user-{i}", "test", {"data": i})
        assert len(cache._local) <= MAX_LOCAL_ENTRIES
