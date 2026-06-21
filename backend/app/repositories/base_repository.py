"""Base Firestore repository providing standard CRUD operations.

All domain-specific repositories inherit from this class to
interact with Google Cloud Firestore collections.
"""

from __future__ import annotations

from typing import Any

from google.cloud import firestore


class BaseRepository:
    """Generic Firestore document repository with CRUD and query support.

    Args:
        db: A Firestore client instance.
        collection: The Firestore collection name.
    """

    def __init__(self, db: firestore.Client, collection: str) -> None:
        self._db = db
        self._collection = db.collection(collection)

    def get(self, doc_id: str) -> dict[str, Any] | None:
        """Retrieve a single document by ID.

        Args:
            doc_id: The Firestore document ID.

        Returns:
            Document data with 'id' field, or None if not found.
        """
        doc = self._collection.document(doc_id).get()
        return {"id": doc.id, **doc.to_dict()} if doc.exists else None

    def set(self, doc_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create or overwrite a document.

        Args:
            doc_id: The Firestore document ID.
            data: The document data to write.

        Returns:
            The written data dictionary.
        """
        self._collection.document(doc_id).set(data)
        return data

    def update(self, doc_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Partially update an existing document.

        Merges the update locally to avoid a second Firestore round-trip.

        Args:
            doc_id: The Firestore document ID.
            data: Fields to update.

        Returns:
            The full updated document, or None if not found.
        """
        doc_ref = self._collection.document(doc_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        doc_ref.update(data)
        return {"id": doc.id, **doc.to_dict(), **data}

    def delete(self, doc_id: str) -> None:
        """Delete a document by ID.

        Args:
            doc_id: The Firestore document ID.
        """
        self._collection.document(doc_id).delete()

    def query(
        self,
        filters: list[tuple[str, str, Any]] | None = None,
        order_by: str | tuple[str, str] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a filtered, ordered, and paginated query.

        Args:
            filters: List of (field, operator, value) tuples.
            order_by: Field name or (field, direction) tuple.
            limit: Maximum number of documents to return.
            cursor: Document ID to start after (for pagination).

        Returns:
            List of matching documents with 'id' fields.
        """
        query_ref = self._collection
        if filters:
            for field, operator, value in filters:
                query_ref = query_ref.where(field, operator, value)
        if order_by:
            if isinstance(order_by, tuple):
                field, direction = order_by
                query_ref = query_ref.order_by(field, direction=direction)
            else:
                query_ref = query_ref.order_by(order_by)
        if cursor:
            doc_snapshot = self._collection.document(cursor).get()
            if doc_snapshot.exists:
                query_ref = query_ref.start_after(doc_snapshot)
        if limit:
            query_ref = query_ref.limit(limit)
        docs = query_ref.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    def count(self, filters: list[tuple[str, str, Any]] | None = None) -> int:
        """Count documents matching the given filters.

        Args:
            filters: Optional list of (field, operator, value) tuples.

        Returns:
            The number of matching documents.
        """
        query_ref = self._collection
        if filters:
            for field, operator, value in filters:
                query_ref = query_ref.where(field, operator, value)
        count_query = query_ref.count()
        result = count_query.get()
        return result[0].value


__all__ = ["BaseRepository"]
