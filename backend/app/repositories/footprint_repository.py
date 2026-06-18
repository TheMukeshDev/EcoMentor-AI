from datetime import datetime, timezone

from app.repositories.base_repository import BaseRepository


class FootprintRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "footprints")

    def find_by_user_id(self, user_id, limit=None):
        return self.query(
            filters=[("uid", "==", user_id)],
            order_by=("created_at", "DESCENDING"),
            limit=limit,
        )

    def find_latest_by_user(self, user_id):
        results = self.find_by_user_id(user_id, limit=1)
        return results[0] if results else None

    def upsert_daily_footprint(self, user_id, date_str, carbon_score, breakdown):
        existing = self.query(
            filters=[
                ("uid", "==", user_id),
                ("date", "==", date_str),
            ],
        )
        if existing:
            doc_id = existing[0].get("id", existing[0].get("doc_id"))
            if doc_id:
                self.update(
                    doc_id,
                    {
                        "carbon_score": carbon_score,
                        "breakdown": breakdown,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                return
        doc = {
            "uid": user_id,
            "date": date_str,
            "carbon_score": carbon_score,
            "breakdown": breakdown,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.set(f"{user_id}_{date_str}", doc)
