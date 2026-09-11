from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any, BinaryIO, Protocol

import boto3  # type: ignore[import-untyped]
from botocore.client import Config  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]
from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings


class ObjectStorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredObjectMetadata:
    size_bytes: int
    content_type: str


class PrivateObjectStorage(Protocol):
    bucket: str

    def upload_pdf(self, file: BinaryIO, key: str) -> None: ...

    def create_pdf_upload_url(self, key: str, size_bytes: int, expires_in_seconds: int) -> str: ...

    def get_object_metadata(self, bucket: str, key: str) -> StoredObjectMetadata: ...

    def download_pdf(self, bucket: str, key: str) -> bytes: ...

    def create_pdf_view_url(self, bucket: str, key: str, expires_in_seconds: int) -> str: ...

    def delete_pdf(self, bucket: str, key: str) -> None: ...


class S3ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        endpoint = settings.object_storage_endpoint
        bucket = settings.object_storage_bucket
        access_key = settings.object_storage_access_key
        secret_key = settings.object_storage_secret_key
        if endpoint is None or bucket is None or access_key is None or secret_key is None:
            raise RuntimeError("Object storage is not configured")

        self.bucket = bucket

        def create_client(endpoint_url: str) -> Any:
            return boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                region_name=settings.object_storage_region,
                aws_access_key_id=access_key.get_secret_value(),
                aws_secret_access_key=secret_key.get_secret_value(),
                config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
            )

        self._client = create_client(endpoint)
        public_endpoint = settings.object_storage_public_endpoint
        self._presigning_client = (
            self._client
            if public_endpoint is None or public_endpoint == endpoint
            else create_client(public_endpoint)
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

    def create_pdf_upload_url(self, key: str, size_bytes: int, expires_in_seconds: int) -> str:
        try:
            return str(
                self._presigning_client.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": key,
                        "ContentType": "application/pdf",
                        "ContentLength": size_bytes,
                    },
                    ExpiresIn=expires_in_seconds,
                )
            )
        except (BotoCoreError, ClientError, OSError) as error:
            raise ObjectStorageError("Could not create document upload URL") from error

    def get_object_metadata(self, bucket: str, key: str) -> StoredObjectMetadata:
        try:
            response = self._client.head_object(Bucket=bucket, Key=key)
            return StoredObjectMetadata(
                size_bytes=int(response["ContentLength"]),
                content_type=str(response.get("ContentType", "")),
            )
        except (BotoCoreError, ClientError, OSError, KeyError, TypeError, ValueError) as error:
            raise ObjectStorageError("Could not inspect document") from error

    def download_pdf(self, bucket: str, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=bucket, Key=key)
            return bytes(response["Body"].read())
        except (BotoCoreError, ClientError, OSError) as error:
            raise ObjectStorageError("Could not retrieve document") from error

    def create_pdf_view_url(self, bucket: str, key: str, expires_in_seconds: int) -> str:
        try:
            return str(
                self._client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": bucket,
                        "Key": key,
                        "ResponseContentType": "application/pdf",
                        "ResponseContentDisposition": "inline",
                        "ResponseCacheControl": "private, no-store",
                    },
                    ExpiresIn=expires_in_seconds,
                )
            )
        except (BotoCoreError, ClientError, OSError) as error:
            raise ObjectStorageError("Could not create document view URL") from error

    def delete_pdf(self, bucket: str, key: str) -> None:
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
        except (BotoCoreError, ClientError, OSError) as error:
            raise ObjectStorageError("Could not delete document") from error


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
