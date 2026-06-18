from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "reports")

    def find_by_user_id(self, user_id):
        results = self.query(filters=[("uid", "==", user_id)])
        results.sort(key=lambda x: x.get("generated_at", ""), reverse=False)
        return results
