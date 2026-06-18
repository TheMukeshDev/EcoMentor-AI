from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "users")

    def find_by_email(self, email):
        results = self.query(filters=[("email", "==", email)])
        return results[0] if results else None
