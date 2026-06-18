from app.repositories.base_repository import BaseRepository


class ChallengeRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "challenges")

    def find_active(self):
        pass

    def find_by_difficulty(self, level):
        pass
