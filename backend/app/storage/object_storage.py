from functools import lru_cache
from typing import Annotated, BinaryIO, Protocol

import boto3  # type: ignore[import-untyped]
from botocore.client import Config  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]
from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings


class ObjectStorageError(RuntimeError):
    pass


class PrivateObjectStorage(Protocol):
    bucket: str

    def upload_pdf(self, file: BinaryIO, key: str) -> None: ...


class S3ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        if (
            settings.object_storage_bucket is None
            or settings.object_storage_access_key is None
            or settings.object_storage_secret_key is None
        ):
            raise RuntimeError("Object storage is not configured")

        self.bucket = settings.object_storage_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.object_storage_endpoint,
            region_name=settings.object_storage_region,
            aws_access_key_id=settings.object_storage_access_key.get_secret_value(),
            aws_secret_access_key=settings.object_storage_secret_key.get_secret_value(),
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def upload_pdf(self, file: BinaryIO, key: str) -> None:
        try:
            self._client.upload_fileobj(
                file,
                self.bucket,
                key,
                ExtraArgs={"ContentType": "application/pdf"},
            )
        except (BotoCoreError, ClientError, OSError) as error:
            raise ObjectStorageError("Could not store document") from error


@lru_cache
def _get_s3_object_storage() -> S3ObjectStorage:
    return S3ObjectStorage(get_settings())


def get_object_storage() -> PrivateObjectStorage:
    try:
        return _get_s3_object_storage()
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is not configured",
        ) from error


ObjectStorage = Annotated[PrivateObjectStorage, Depends(get_object_storage)]
