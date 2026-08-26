from collections.abc import Sequence


def make_text_pdf(
    pages: Sequence[Sequence[str]],
    *,
    title: str = "Document immobilier",
    author: str = "Cabinet de diagnostics",
) -> bytes:
    """Build a small valid PDF without adding a test-only PDF dependency."""

    objects: list[bytes] = []

    def add_object(value: bytes) -> int:
        objects.append(value)
        return len(objects)

    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"")
    pages_id = len(objects)
    page_ids: list[int] = []

    for lines in pages:
        commands = ["BT", "/F1 12 Tf", "50 790 Td"]
        for index, line in enumerate(lines):
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if index:
                commands.append("0 -20 Td")
            commands.append(f"({escaped}) Tj")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1")
        content_id = add_object(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )
        page_id = add_object(
            b"<< /Type /Page /Parent "
            + str(pages_id).encode()
            + b" 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 "
            + str(font_id).encode()
            + b" 0 R >> >> /Contents "
            + str(content_id).encode()
            + b" 0 R >>"
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        b"<< /Type /Pages /Kids ["
        + b" ".join(str(page_id).encode() + b" 0 R" for page_id in page_ids)
        + b"] /Count "
        + str(len(page_ids)).encode()
        + b" >>"
    )
    info_id = add_object(
        b"<< /Title ("
        + title.encode("latin-1")
        + b") /Author ("
        + author.encode("latin-1")
        + b") >>"
    )
    catalog_id = add_object(b"<< /Type /Catalog /Pages " + str(pages_id).encode() + b" 0 R >>")

    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, value in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{object_number} 0 obj\n".encode())
        data.extend(value)
        data.extend(b"\nendobj\n")

    xref_offset = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R "
            f"/Info {info_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(data)


DPE_PDF = make_text_pdf(
    [
        [
            "DIAGNOSTIC DE PERFORMANCE ENERGETIQUE",
            "Classe energie E",
            "Consommation 280 kWh/m2/an",
        ],
        [
            "Estimation des couts annuels d'energie",
            "Montant minimum 1500 EUR",
            "Montant maximum 2100 EUR",
        ],
    ],
    title="DPE appartement",
)

AG_MINUTES_PDF = make_text_pdf(
    [
        ["PROCES-VERBAL ASSEMBLEE GENERALE", "Resolution 1 approuvee", "Budget 12500 EUR"],
        ["TRAVAUX DE TOITURE", "Resolution 2 reportee", "Devis 48000 EUR"],
        ["FIN DE SEANCE", "Signature du syndic"],
    ],
    title="Proces-verbal AG 2025",
    author="Syndic Exemple",
)
