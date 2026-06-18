from google.cloud import firestore


class BaseRepository:
    def __init__(self, db: firestore.Client, collection: str):
        self._db = db
        self._collection = db.collection(collection)

    def get(self, doc_id: str):
        pass

    def set(self, doc_id: str, data: dict):
        pass

    def update(self, doc_id: str, data: dict):
        pass

    def delete(self, doc_id: str):
        pass

    def query(self, filters=None, order_by=None, limit=None):
        pass
