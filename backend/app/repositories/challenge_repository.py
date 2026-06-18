from app.repositories.base_repository import BaseRepository


class ChallengeRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "challenges")

    def find_active(self):
        return self.query(filters=[("completed", "==", False)])

    def find_by_difficulty(self, difficulty):
        return self.query(filters=[("difficulty", "==", difficulty)])
