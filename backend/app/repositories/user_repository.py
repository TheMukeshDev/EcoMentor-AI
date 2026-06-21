from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "users")

    def find_by_email(self, email: str) -> dict | None:
        """Find user by email."""
        results = self.query(filters=[("email", "==", email)], limit=1)
        return results[0] if results else None

    def get_batch(self, doc_ids):
        refs = [self._collection.document(did) for did in doc_ids]
        snapshots = self._db.get_all(refs)
        return [{"id": s.id, **s.to_dict()} for s in snapshots if s and s.exists]
