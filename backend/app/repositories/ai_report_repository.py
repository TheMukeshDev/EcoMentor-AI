from datetime import datetime, timezone

from app.repositories.base_repository import BaseRepository


class AIReportRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "ai_reports")

    def find_valid_by_user_and_type(self, user_id, report_type):
        now = datetime.now(timezone.utc).isoformat()
        results = self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
            ],
        )
        filtered = [
            r for r in results 
            if r.get("expires_at", "") >= now
        ]
        filtered.sort(key=lambda x: x.get("generated_at", ""), reverse=False)
        return filtered

    def find_by_user_and_type(self, user_id, report_type):
        results = self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
            ],
        )
        results.sort(key=lambda x: x.get("generated_at", ""), reverse=False)
        return results
