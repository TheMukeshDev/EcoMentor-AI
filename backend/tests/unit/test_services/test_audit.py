import pytest


class TestAudit:
    def test_log_event_does_not_raise(self):
        from app.utils.audit import log_event

        log_event(
            "test_event", user_id="user-1", ip="127.0.0.1", details={"key": "value"}
        )
        assert True

    def test_log_event_without_user(self):
        from app.utils.audit import log_event

        log_event("anonymous_event")
        assert True


class TestAuditIntegration:
    def test_log_event_is_callable(self):
        from app.utils.audit import log_event
        import logging

        logger = logging.getLogger("audit")
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        log_event(
            "test_integration",
            user_id="user-1",
            ip="127.0.0.1",
            details={"action": "test"},
        )
        logger.removeHandler(handler)
        assert True
