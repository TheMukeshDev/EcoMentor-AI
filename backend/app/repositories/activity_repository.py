from app.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "activities")

    def find_by_user_id(self, user_id):
        pass

    def find_by_user_and_date_range(self, user_id, start, end):
        pass
