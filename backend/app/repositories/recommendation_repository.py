from app.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "recommendations")

    def find_by_user_id(self, user_id):
        pass

    def find_by_category(self, category):
        pass
