from app.repositories.base_repository import BaseRepository


class CarbonHistoryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "carbon_history")

    def find_by_user_id(self, user_id, limit=None):
        return self.query(
            filters=[("uid", "==", user_id)],
            order_by="date",
            limit=limit,
        )

    def find_by_user_and_date_range(self, user_id, start, end):
        return self.query(
            filters=[
                ("uid", "==", user_id),
                ("date", ">=", start),
                ("date", "<=", end),
            ],
            order_by="date",
        )

    def find_by_user_and_date(self, user_id, date):
        results = self.query(
            filters=[
                ("uid", "==", user_id),
                ("date", "==", date),
            ],
        )
        return results[0] if results else None
