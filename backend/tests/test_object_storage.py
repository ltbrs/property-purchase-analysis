from urllib.parse import parse_qs, urlparse

from pydantic import SecretStr

from app.core.config import Settings
from app.storage.object_storage import S3ObjectStorage


def test_pdf_upload_url_uses_public_endpoint_and_signs_type_and_size() -> None:
    storage = S3ObjectStorage(
        Settings(
            object_storage_endpoint="http://object-storage:9000",
            object_storage_public_endpoint="https://storage.example.test/s3",
            object_storage_bucket="private-documents",
            object_storage_region="eu-west-3",
            object_storage_access_key=SecretStr("test-access-key"),
            object_storage_secret_key=SecretStr("test-secret-key"),
        )
    )

    url = storage.create_pdf_upload_url("cases/upload.pdf", 1234, 300)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "storage.example.test"
    assert parsed.path == "/s3/private-documents/cases/upload.pdf"
    assert query["X-Amz-Expires"] == ["300"]
    assert query["X-Amz-SignedHeaders"] == ["content-length;content-type;host"]
