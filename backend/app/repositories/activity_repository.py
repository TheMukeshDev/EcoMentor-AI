from app.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "activities")

    def find_by_user_id(self, user_id, limit=None, cursor=None):
        return self.query(
            filters=[("uid", "==", user_id)],
            order_by=("date", "DESCENDING"),
            limit=limit,
            cursor=cursor,
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
