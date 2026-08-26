"""Private S3-compatible document storage boundary."""

from app.storage.object_storage import ObjectStorageError, PrivateObjectStorage

__all__ = ["ObjectStorageError", "PrivateObjectStorage"]
