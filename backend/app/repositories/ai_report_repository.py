from datetime import datetime, timezone

from app.repositories.base_repository import BaseRepository


class AIReportRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "ai_reports")

    def find_valid_by_user_and_type(self, user_id, report_type):
        now = datetime.now(timezone.utc).isoformat()
        return self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
                ("expires_at", ">=", now),
            ],
            order_by="generated_at",
        )

    def find_by_user_and_type(self, user_id, report_type):
        return self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
            ],
            order_by="generated_at",
        )
