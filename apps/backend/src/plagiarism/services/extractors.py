"""
Document Text Extraction Service
Supports multi-page PDF (pypdf), DOCX (python-docx), and TXT text extraction.
Enforces format magic validation, zip bomb protection, and encrypted PDF detection.
"""

import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import pypdf
import docx

from plagiarism.core.errors import BadRequestError


@dataclass
class DocumentExtractionResult:
    raw_text: str
    page_count: int
    char_count: int
    page_texts: List[Tuple[int, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    extractor_name: str = "default-extractor"


def validate_format_magic(file_path: Path, extension: str) -> None:
    """
    Validates file headers and structural signatures against declared format.
    Rejects spoofed extensions and corrupted files.
    """
    ext = extension.lower().lstrip(".")
    with open(file_path, "rb") as f:
        header = f.read(1024)

    if ext == "pdf":
        if not header.startswith(b"%PDF-"):
            raise BadRequestError(
                "Invalid PDF format: file header does not match %PDF- signature",
                code="CORRUPTED_DOCUMENT"
            )
    elif ext == "docx":
        if not header.startswith(b"PK\x03\x04"):
            raise BadRequestError(
                "Invalid DOCX format: file is not a valid ZIP/OpenXML archive",
                code="CORRUPTED_DOCUMENT"
            )
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                names = z.namelist()
                if "word/document.xml" not in names:
                    raise BadRequestError(
                        "Invalid DOCX structure: missing word/document.xml",
                        code="CORRUPTED_DOCUMENT"
                    )
        except zipfile.BadZipFile:
            raise BadRequestError("Malformed or corrupted DOCX archive", code="CORRUPTED_DOCUMENT")
    elif ext == "txt":
        # Ensure it's not arbitrary binary data by checking for excessive null bytes
        if b"\x00" in header[:256] and not (header.startswith(b"\xff\xfe") or header.startswith(b"\xfe\xff")):
            raise BadRequestError(
                "Invalid plain text: binary bytes or null characters detected",
                code="UNSUPPORTED_ENCODING"
            )
    else:
        raise BadRequestError(
            f"Unsupported document format '.{ext}'. Supported formats are: PDF, DOCX, TXT",
            code="UNSUPPORTED_FORMAT"
        )


def extract_pdf(file_path: Path) -> DocumentExtractionResult:
    """
    Extracts text from multi-page PDF documents using pypdf.
    Detects password protection and reports empty/scanned PDFs.
    """
    try:
        reader = pypdf.PdfReader(str(file_path))
    except Exception as e:
        raise BadRequestError(f"Failed to open PDF document: {str(e)}", code="CORRUPTED_DOCUMENT")

    if reader.is_encrypted:
        try:
            # Try decrypting with empty password
            decrypted = reader.decrypt("")
            if decrypted == 0:
                raise BadRequestError(
                    "Password-protected or encrypted PDFs are not supported",
                    code="ENCRYPTED_DOCUMENT"
                )
        except Exception:
            raise BadRequestError(
                "Password-protected or encrypted PDFs are not supported",
                code="ENCRYPTED_DOCUMENT"
            )

    page_count = len(reader.pages)
    if page_count == 0:
        return DocumentExtractionResult(
            raw_text="",
            page_count=0,
            char_count=0,
            warnings=["PDF document contains 0 pages"],
            extractor_name="pypdf 6.20.1"
        )

    page_texts: List[Tuple[int, str]] = []
    full_text_chunks: List[str] = []
    warnings: List[str] = []

    for i, page in enumerate(reader.pages, start=1):
        try:
            extracted = page.extract_text() or ""
            # Canonicalize line endings
            cleaned_page = extracted.replace("\r\n", "\n").replace("\r", "\n").strip()
            page_texts.append((i, cleaned_page))
            if cleaned_page:
                full_text_chunks.append(cleaned_page)
        except Exception as e:
            warnings.append(f"Page {i} text extraction warning: {str(e)}")
            page_texts.append((i, ""))

    raw_text = "\n\n".join(full_text_chunks).strip()
    if not raw_text:
        warnings.append("No selectable text found in document (scanned or image-only PDF)")

    return DocumentExtractionResult(
        raw_text=raw_text,
        page_count=page_count,
        char_count=len(raw_text),
        page_texts=page_texts,
        warnings=warnings,
        extractor_name="pypdf 6.20.1"
    )


def extract_docx(file_path: Path) -> DocumentExtractionResult:
    """
    Extracts text from Word DOCX documents using python-docx.
    Includes zip bomb protection and table cell extraction.
    """
    # Guard against zip bombs: examine uncompressed size
    try:
        with zipfile.ZipFile(file_path, "r") as z:
            uncompressed_size = sum(item.file_size for item in z.infolist())
            compressed_size = max(1, os.path.getsize(file_path))
            ratio = uncompressed_size / compressed_size
            if ratio > 100 or uncompressed_size > 50 * 1024 * 1024:
                raise BadRequestError(
                    "DOCX archive exceeded safety expansion ratio (zip bomb defense triggered)",
                    code="SECURITY_VIOLATION"
                )
    except BadRequestError:
        raise
    except Exception as e:
        raise BadRequestError(f"Corrupted DOCX archive: {str(e)}", code="CORRUPTED_DOCUMENT")

    try:
        doc = docx.Document(str(file_path))
    except Exception as e:
        raise BadRequestError(f"Failed to parse DOCX content: {str(e)}", code="CORRUPTED_DOCUMENT")

    paragraphs_text = []
    warnings = []

    # 1. Extract paragraphs
    for p in doc.paragraphs:
        t = p.text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if t:
            paragraphs_text.append(t)

    # 2. Extract tables
    for table in doc.tables:
        for row in table.rows:
            row_cells = [c.text.replace("\r\n", "\n").replace("\r", "\n").strip() for c in row.cells]
            row_text = " | ".join(c for c in row_cells if c)
            if row_text:
                paragraphs_text.append(row_text)

    raw_text = "\n\n".join(paragraphs_text).strip()
    if not raw_text:
        warnings.append("No text content found in DOCX document")

    # Estimated page count: standard ~2000 chars per page
    estimated_pages = max(1, (len(raw_text) + 1999) // 2000)

    return DocumentExtractionResult(
        raw_text=raw_text,
        page_count=estimated_pages,
        char_count=len(raw_text),
        page_texts=[(1, raw_text)],
        warnings=warnings,
        extractor_name="python-docx 1.2.0"
    )


def extract_txt(file_path: Path) -> DocumentExtractionResult:
    """
    Extracts text from plain-text TXT files.
    Supports UTF-8, UTF-8 with BOM, and UTF-16 encodings.
    """
    encodings_to_try = ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin-1"]
    raw_bytes = open(file_path, "rb").read()
    raw_text = None
    warnings = []
    used_encoding = "utf-8"

    for enc in encodings_to_try:
        try:
            raw_text = raw_bytes.decode(enc)
            used_encoding = enc
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if raw_text is None:
        raise BadRequestError(
            "Unable to decode text file with supported character encodings (UTF-8, UTF-16)",
            code="UNSUPPORTED_ENCODING"
        )

    if used_encoding not in ("utf-8-sig", "utf-8", "utf-16"):
        warnings.append(f"Document decoded using fallback encoding: {used_encoding}")

    # Canonicalize line endings
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    estimated_pages = max(1, (len(raw_text) + 1999) // 2000)

    return DocumentExtractionResult(
        raw_text=raw_text,
        page_count=estimated_pages,
        char_count=len(raw_text),
        page_texts=[(1, raw_text)],
        warnings=warnings,
        extractor_name="plain-text-reader"
    )


def extract_document(file_path: Path, extension: str) -> DocumentExtractionResult:
    """
    Validates magic bytes and dispatches to appropriate extractor for PDF, DOCX, or TXT.
    """
    ext = extension.lower().lstrip(".")
    validate_format_magic(file_path, ext)

    if ext == "pdf":
        return extract_pdf(file_path)
    elif ext == "docx":
        return extract_docx(file_path)
    elif ext == "txt":
        return extract_txt(file_path)
    else:
        raise BadRequestError(f"Unsupported format '.{ext}'", code="UNSUPPORTED_FORMAT")
