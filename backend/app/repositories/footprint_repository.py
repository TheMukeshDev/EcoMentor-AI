from app.repositories.base_repository import BaseRepository


class FootprintRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "footprints")

    def find_by_user_id(self, user_id):
        pass

    def find_latest_by_user(self, user_id):
        pass
