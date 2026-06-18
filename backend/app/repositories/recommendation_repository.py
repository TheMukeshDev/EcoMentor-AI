from app.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "recommendations")

    def find_by_user_id(self, user_id, limit=None):
        return self.query(
            filters=[("uid", "==", user_id)],
            order_by=("created_at", "DESCENDING"),
            limit=limit,
        )

    def find_by_category(self, category):
        return self.query(
            filters=[("category", "==", category)],
            order_by="created_at",
        )

    def find_valid_by_user_and_type(self, user_id, report_type):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        return self.query(
            filters=[
                ("uid", "==", user_id),
                ("type", "==", report_type),
                ("expires_at", ">=", now),
            ],
            order_by=("generated_at", "DESCENDING"),
        )
