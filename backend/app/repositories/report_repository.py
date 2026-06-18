from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "reports")

    def find_by_user_id(self, user_id):
        return self.query(filters=[("uid", "==", user_id)], order_by="generated_at")
