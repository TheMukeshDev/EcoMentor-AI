from app.repositories.base_repository import BaseRepository


class CarbonHistoryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "carbon_history")

    def find_by_user_id(self, user_id, limit=None):
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        results.sort(key=lambda x: x.get("date", ""), reverse=False)
        if limit is not None:
            results = results[:limit]
        return results

    def find_by_user_and_date_range(self, user_id, start, end):
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        filtered = [
            r for r in results 
            if r.get("date", "") >= start and r.get("date", "") <= end
        ]
        filtered.sort(key=lambda x: x.get("date", ""), reverse=False)
        return filtered

    def find_by_user_and_date(self, user_id, date):
        results = self.query(
            filters=[
                ("uid", "==", user_id),
                ("date", "==", date),
            ],
        )
        return results[0] if results else None
