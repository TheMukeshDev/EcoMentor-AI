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
            if isinstance(order_by, tuple):
                field, direction = order_by
                query = query.order_by(field, direction=direction)
            else:
                query = query.order_by(order_by)
        if limit:
            query = query.limit(limit)
        docs = query.stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]

    def paginated_query(self, filters=None, order_by=None, page=1, page_size=20):
        query = self._collection
        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)
        if order_by:
            if isinstance(order_by, tuple):
                field, direction = order_by
                query = query.order_by(field, direction=direction)
            else:
                query = query.order_by(order_by)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        docs = query.stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]

    def count(self, filters=None):
        query = self._collection
        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)
        return len(list(query.stream()))

    def list_all(self):
        docs = self._collection.stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
