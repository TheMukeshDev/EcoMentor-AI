from google.cloud import firestore


class BaseRepository:
    def __init__(self, db: firestore.Client, collection: str):
        self._db = db
        self._collection = db.collection(collection)

    def get(self, doc_id: str):
        doc = self._collection.document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    def set(self, doc_id: str, data: dict):
        self._collection.document(doc_id).set(data)
        return data

    def update(self, doc_id: str, data: dict):
        self._collection.document(doc_id).update(data)
        return self.get(doc_id)

    def delete(self, doc_id: str):
        self._collection.document(doc_id).delete()

    def query(self, filters=None, order_by=None, limit=None):
        query = self._collection
        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)
        if order_by:
            query = query.order_by(order_by)
        if limit:
            query = query.limit(limit)
        docs = query.stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]

    def list_all(self):
        docs = self._collection.stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
