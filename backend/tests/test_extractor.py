"""Tests for backend/document_processing/extractor.py."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from backend.document_processing.extractor import (
    extract_text,
    extract_text_from_txt,
)


# ---------------------------------------------------------------------------
# Plain-text extraction (no external library needed)
# ---------------------------------------------------------------------------


class TestExtractTextFromTxt:
    def test_reads_content(self, txt_file: str, sample_text: str):
        result = extract_text_from_txt(txt_file)
        assert result == sample_text

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.txt"
        p.write_text("", encoding="utf-8")
        assert extract_text_from_txt(str(p)) == ""

    def test_unicode_content(self, tmp_path):
        content = "こんにちは世界 – résumé – naïve"
        p = tmp_path / "unicode.txt"
        p.write_text(content, encoding="utf-8")
        result = extract_text_from_txt(str(p))
        assert result == content

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(Exception):
            extract_text_from_txt(str(tmp_path / "nonexistent.txt"))


# ---------------------------------------------------------------------------
# PDF extraction (fitz is stubbed via conftest.py)
# ---------------------------------------------------------------------------


class TestExtractTextFromPdf:
    def test_returns_concatenated_pages(self, tmp_path):
        """fitz.open is a MagicMock; configure it to yield two pages."""
        fake_page_1 = MagicMock()
        fake_page_1.get_text.return_value = "Page one content."
        fake_page_2 = MagicMock()
        fake_page_2.get_text.return_value = "Page two content."

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([fake_page_1, fake_page_2]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        import fitz  # noqa: PLC0415 – stub from conftest

        with patch.object(fitz, "open", return_value=mock_doc):
            from backend.document_processing.extractor import extract_text_from_pdf  # noqa: PLC0415

            result = extract_text_from_pdf(str(tmp_path / "fake.pdf"))

        assert "Page one content." in result
        assert "Page two content." in result


# ---------------------------------------------------------------------------
# DOCX extraction (docx is stubbed via conftest.py)
# ---------------------------------------------------------------------------


class TestExtractTextFromDocx:
    def test_returns_paragraphs(self, tmp_path):
        """docx.Document is a MagicMock; configure it to yield paragraphs."""
        para1 = MagicMock()
        para1.text = "First paragraph."
        para2 = MagicMock()
        para2.text = "Second paragraph."
        para3 = MagicMock()
        para3.text = "  "  # whitespace-only – should be skipped

        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = [para1, para2, para3]

        import docx  # noqa: PLC0415 – stub from conftest

        with patch.object(docx, "Document", return_value=mock_doc_instance):
            from backend.document_processing.extractor import extract_text_from_docx  # noqa: PLC0415

            result = extract_text_from_docx(str(tmp_path / "fake.docx"))

        assert "First paragraph." in result
        assert "Second paragraph." in result
        # Whitespace-only paragraphs must be excluded
        assert result.strip() != ""
        assert "  " not in result.split("\n")


# ---------------------------------------------------------------------------
# Dispatcher: extract_text()
# ---------------------------------------------------------------------------


class TestExtractText:
    def test_routes_txt(self, txt_file: str):
        result = extract_text(txt_file, "txt")
        assert len(result) > 0

    def test_routes_text_plain_mime(self, txt_file: str):
        result = extract_text(txt_file, "text/plain")
        assert len(result) > 0

    def test_routes_pdf(self, tmp_path):
        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        import fitz  # noqa: PLC0415

        with patch.object(fitz, "open", return_value=mock_doc):
            result = extract_text(str(tmp_path / "x.pdf"), "pdf")
        assert isinstance(result, str)

    def test_routes_pdf_mime(self, tmp_path):
        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        import fitz  # noqa: PLC0415

        with patch.object(fitz, "open", return_value=mock_doc):
            result = extract_text(str(tmp_path / "x.pdf"), "application/pdf")
        assert isinstance(result, str)

    def test_unsupported_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text("/any/path", "image/png")
