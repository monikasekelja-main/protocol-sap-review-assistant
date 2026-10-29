"""Bounded, location-preserving extraction. Run via the isolated CLI entrypoint."""

import io
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

MAX_BLOCKS = 6000
MAX_CHARS = 600_000


class ExtractionError(ValueError):
    pass


def extract(content, name):
    blocks, limitations = [], []
    char_count = 0

    def add(text, location, kind="paragraph"):
        nonlocal char_count
        char_count += len(text)
        if text.strip():
            blocks.append(
                {"id": f"b{len(blocks) + 1}", "text": text, "location": location, "kind": kind}
            )
        if len(blocks) > MAX_BLOCKS or char_count > MAX_CHARS:
            raise ExtractionError("Document exceeds supported extraction size.")

    if name.lower().endswith(".docx") and content.startswith(b"PK"):
        from docx import Document
        from docx.table import Table

        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if (
                len(archive.infolist()) > 2000
                or sum(x.file_size for x in archive.infolist()) > 100 * 1024 * 1024
            ):
                raise ExtractionError("DOCX archive exceeds safe expansion limits.")
            if "word/document.xml" not in archive.namelist():
                raise ExtractionError("This file is not a Word document.")
            for part in archive.namelist():
                if part.startswith("word/") and part.endswith(".xml"):
                    root = ElementTree.fromstring(archive.read(part))
                    tags = {node.tag.rsplit("}", 1)[-1] for node in root.iter()}
                    if tags & {"ins", "del", "moveFrom", "moveTo"}:
                        raise ExtractionError(
                            "Accept or reject tracked changes before uploading this DOCX."
                        )
                    if tags & {
                        "txbxContent",
                        "altChunk",
                        "object",
                        "footnoteReference",
                        "endnoteReference",
                    }:
                        limitations.append(
                            "Embedded content, text boxes, footnotes or endnotes may be omitted; related checks are incomplete."
                        )
            if any(
                x.startswith("word/header") or x.startswith("word/footer")
                for x in archive.namelist()
            ):
                limitations.append(
                    "Headers and footers are not assessed. Metadata must be confirmed by the user."
                )
        doc = Document(io.BytesIO(content))

        def walk(container, path):
            for i, element in enumerate(container.iter_inner_content(), 1):
                loc = f"{path} / block {i}"
                if isinstance(element, Table):
                    # Keep row/column links without flattening merged cells into invented facts.
                    for r, row in enumerate(element.rows, 1):
                        values = [cell.text for cell in row.cells]
                        add(" | ".join(values), f"{loc} / table row {r}", "table")
                        seen = set()
                        for c, cell in enumerate(row.cells, 1):
                            if id(cell._tc) in seen:
                                continue
                            seen.add(id(cell._tc))
                            if cell.tables:
                                walk(cell, f"{loc} / row {r} / cell {c}")
                    limitations.append(
                        "Schedule tables require manual verification of merged headers and footnotes; schedule checks remain partial."
                    )
                else:
                    add(element.text, loc)

        walk(doc, "DOCX body")
    elif name.lower().endswith(".pdf") and content.startswith(b"%PDF-"):
        import pdfplumber

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if len(pdf.pages) > 250:
                raise ExtractionError("PDF exceeds the 250-page limit.")
            for page in pdf.pages:
                text = page.extract_text(layout=False) or ""
                if not text.strip():
                    limitations.append(
                        f"PDF page {page.page_number} has no readable text; OCR is not supported."
                    )
                for line in page.extract_text_lines():
                    add(
                        line["text"],
                        f"PDF page {page.page_number} · bbox {tuple(round(line[k], 1) for k in ('x0', 'top', 'x1', 'bottom'))}",
                    )
                for table in page.find_tables():
                    for i, row in enumerate(table.extract(), 1):
                        add(
                            " | ".join(cell or "" for cell in row),
                            f"PDF page {page.page_number} / table {tuple(table.bbox)} / row {i}",
                            "table",
                        )
            limitations.append(
                "PDF reading order and undetected tables cannot be guaranteed; assessment schedule checks require manual verification."
            )
    else:
        raise ExtractionError("File contents do not match a supported DOCX or PDF.")
    if not blocks:
        raise ExtractionError(
            "No usable text was extracted. Scans and image-only documents are unsupported."
        )
    if sum(len(b["text"]) for b in blocks) > MAX_CHARS:
        raise ExtractionError("Document exceeds the 600,000-character extraction limit.")
    text = "\n".join(b["text"] for b in blocks)
    version = re.search(r"\bversion\s*[:v]?\s*([\w.\-]+)", text, re.I)
    date = re.search(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", text)
    metadata = {
        "title": blocks[0]["text"][:200],
        "version": version.group(1) if version else "Unknown",
        "date": date.group(0) if date else "Unknown",
    }
    return {"blocks": blocks, "limitations": list(dict.fromkeys(limitations)), "metadata": metadata}


if __name__ == "__main__":
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    # macOS rejects address-space limits; enforce a hard memory cap in Linux containers.
    if sys.platform != "darwin":
        resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024**2, 1536 * 1024**2))
    try:
        result = extract(Path(sys.argv[1]).read_bytes(), sys.argv[2])
        print(json.dumps(result))
    except ExtractionError as exc:
        print(json.dumps({"error": str(exc)}))
    except Exception:
        print(
            json.dumps(
                {
                    "error": "The document could not be safely read. Export a clean DOCX or text PDF and try again."
                }
            )
        )
