from app.repositories.base_repository import BaseRepository


class LeaderboardRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "leaderboard")

    def get_top(self, limit=50):
        return self.query(order_by="points", limit=limit)
