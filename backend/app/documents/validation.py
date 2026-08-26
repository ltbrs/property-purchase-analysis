import hashlib
from dataclasses import dataclass
from pathlib import PurePath

from fastapi import UploadFile

PDF_MIME_TYPES = frozenset({"application/pdf", "application/x-pdf"})
READ_CHUNK_SIZE = 1024 * 1024


class InvalidDocument(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    size_bytes: int
    sha256: str


async def validate_pdf(upload: UploadFile, max_size_bytes: int) -> ValidatedUpload:
    if upload.content_type not in PDF_MIME_TYPES:
        raise InvalidDocument("Seuls les fichiers PDF sont acceptés.")

    raw_filename = upload.filename or ""
    filename = PurePath(raw_filename.replace("\\", "/")).name.strip()
    if not filename or len(filename) > 255 or any(ord(char) < 32 for char in filename):
        raise InvalidDocument("Le nom du fichier est invalide.")

    digest = hashlib.sha256()
    size_bytes = 0
    signature_buffer = b""

    while chunk := await upload.read(READ_CHUNK_SIZE):
        size_bytes += len(chunk)
        if size_bytes > max_size_bytes:
            await upload.seek(0)
            raise InvalidDocument(
                f"Le fichier dépasse la taille maximale de {max_size_bytes // (1024 * 1024)} Mo."
            )
        if len(signature_buffer) < 1024:
            signature_buffer += chunk[: 1024 - len(signature_buffer)]
        digest.update(chunk)

    await upload.seek(0)

    if size_bytes == 0:
        raise InvalidDocument("Le fichier est vide.")
    if b"%PDF-" not in signature_buffer:
        raise InvalidDocument("Le contenu du fichier ne correspond pas à un PDF valide.")

    return ValidatedUpload(
        filename=filename,
        size_bytes=size_bytes,
        sha256=digest.hexdigest(),
    )
