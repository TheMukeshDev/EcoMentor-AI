from app.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "activities")

    def find_by_user_id(self, user_id, limit=None, cursor=None):
        results = self.query(
            filters=[("uid", "==", user_id)],
        )
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        if cursor:
            try:
                idx = next(i for i, r in enumerate(results) if r.get("id") == cursor)
                results = results[idx+1:]
            except StopIteration:
                pass
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
