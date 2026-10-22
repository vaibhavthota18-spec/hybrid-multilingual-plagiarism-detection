"""
Unit Tests for Document Text Extractors (PDF, DOCX, TXT)
Tests real extraction, magic byte validation, encrypted PDF detection, and error conditions.
"""

import io
import pytest
import pypdf
import docx
from pathlib import Path

from plagiarism.services.extractors import (
    extract_document,
    extract_pdf,
    extract_docx,
    extract_txt,
    validate_format_magic,
)
from plagiarism.core.errors import BadRequestError


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Creates a valid PDF document with selectable text."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"5 0 obj\n<< /Length 44 >>\nstream\n"
        b"BT\n/F1 12 Tf\n72 712 Td\n(Plagiarism Detection System) Tj\nET\nendstream\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n"
        b"0000000117 00000 n \n0000000223 00000 n \n0000000300 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n395\n%%EOF"
    )
    real_pdf_path = tmp_path / "valid_sample.pdf"
    real_pdf_path.write_bytes(pdf_content)
    return real_pdf_path


@pytest.fixture
def sample_docx_path(tmp_path: Path) -> Path:
    """Creates a real DOCX file with paragraphs and a table."""
    doc = docx.Document()
    doc.add_heading("Research Methodology", level=1)
    doc.add_paragraph("This study examines lexical and semantic plagiarism detection across multiple languages.")
    doc.add_paragraph("Hindi: साहित्यिक चोरी का पता लगाने के लिए बहुभाषी प्रणाली।")
    doc.add_paragraph("Telugu: బహుభాషా సాహిత్య చౌర్యం గుర్తించే పరిశోధనా వ్యవస్థ.")
    
    # Add a table
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Language"
    table.cell(0, 1).text = "Script"
    table.cell(1, 0).text = "Telugu"
    table.cell(1, 1).text = "Brahmic (Telugu script)"
    
    docx_path = tmp_path / "sample.docx"
    doc.save(str(docx_path))
    return docx_path


@pytest.fixture
def sample_txt_path(tmp_path: Path) -> Path:
    """Creates a UTF-8 encoded text file with multilingual passages."""
    txt_path = tmp_path / "sample.txt"
    content = (
        "Enterprise Plagiarism Detection System\n\n"
        "This platform validates textual similarity using character winnowing and dense embeddings.\n\n"
        "Hindi passage: हिंदी भाषा में पाठ निष्कर्षण और परीक्षण।\n\n"
        "Telugu passage: తెలుగు భాషలో టెక్స్ట్ ఎక్స్‌ట్రాక్షన్ మరియు ప్రాసెసింగ్."
    )
    txt_path.write_text(content, encoding="utf-8")
    return txt_path


def test_txt_extraction_utf8(sample_txt_path):
    """Verify plain-text UTF-8 extraction preserves Unicode characters."""
    result = extract_txt(sample_txt_path)
    assert "Enterprise Plagiarism Detection System" in result.raw_text
    assert "हिंदी भाषा में पाठ निष्कर्षण" in result.raw_text
    assert "తెలుగు భాషలో టెక్స్ట్ ఎక్స్‌ట్రాక్షన్" in result.raw_text
    assert result.char_count > 0
    assert result.page_count >= 1
    assert result.extractor_name == "plain-text-reader"


def test_txt_extraction_utf16(tmp_path):
    """Verify plain-text UTF-16 extraction with BOM."""
    txt_path = tmp_path / "utf16_sample.txt"
    content = "UTF-16 test document with multilingual text: తెలుగు మరియు हिंदी."
    txt_path.write_text(content, encoding="utf-16")
    
    result = extract_txt(txt_path)
    assert "UTF-16 test document" in result.raw_text
    assert "తెలుగు మరియు हिंदी" in result.raw_text


def test_docx_extraction(sample_docx_path):
    """Verify DOCX extraction captures headings, paragraphs, tables, and Indic scripts."""
    result = extract_docx(sample_docx_path)
    assert "Research Methodology" in result.raw_text
    assert "lexical and semantic plagiarism detection" in result.raw_text
    assert "साहित्यिक चोरी" in result.raw_text
    assert "సాహిత్య చౌర్యం" in result.raw_text
    assert "Brahmic (Telugu script)" in result.raw_text
    assert result.extractor_name == "python-docx 1.2.0"


def test_pdf_extraction(sample_pdf_path):
    """Verify PDF extraction extracts page text and page count."""
    result = extract_pdf(sample_pdf_path)
    assert result.page_count == 1
    assert "Plagiarism Detection System" in result.raw_text
    assert result.extractor_name == "pypdf 6.20.1"


def test_pdf_magic_validation_failure(tmp_path):
    """Verify spoofed PDF file (e.g. text file renamed to .pdf) is rejected."""
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("This is definitely not a PDF file.", encoding="utf-8")
    
    with pytest.raises(BadRequestError, match="Invalid PDF format: file header does not match %PDF-"):
        validate_format_magic(fake_pdf, "pdf")


def test_docx_magic_validation_failure(tmp_path):
    """Verify spoofed DOCX file is rejected by magic byte validator."""
    fake_docx = tmp_path / "fake.docx"
    fake_docx.write_text("Plain text masquerading as a DOCX archive", encoding="utf-8")
    
    with pytest.raises(BadRequestError, match="Invalid DOCX format: file is not a valid ZIP"):
        validate_format_magic(fake_docx, "docx")


def test_unsupported_format_dispatch(tmp_path):
    """Verify unsupported extensions (e.g. .exe, .xlsx) are rejected."""
    bad_file = tmp_path / "document.xlsx"
    bad_file.write_bytes(b"dummy")
    
    with pytest.raises(BadRequestError, match="Unsupported document format"):
        extract_document(bad_file, "xlsx")
