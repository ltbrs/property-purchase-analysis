import asyncio
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.documents.validation import InvalidDocument, validate_pdf


def test_pdf_larger_than_configured_limit_is_rejected() -> None:
    upload = UploadFile(
        file=BytesIO(b"%PDF-1.7\n" + b"x" * 32),
        filename="large.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )

    with pytest.raises(InvalidDocument, match="taille maximale"):
        asyncio.run(validate_pdf(upload, max_size_bytes=16))
