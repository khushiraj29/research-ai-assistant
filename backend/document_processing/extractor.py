"""Text extraction utilities for PDF, DOCX, and plain-text documents."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file using PyMuPDF.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        Concatenated text of all pages, separated by newlines.
    """
    try:
        import fitz  # PyMuPDF

        text_parts: list[str] = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)
    except Exception as exc:
        logger.error("Failed to extract text from PDF '%s': %s", file_path, exc)
        raise


def extract_text_from_docx(file_path: str) -> str:
    """Extract all paragraph text from a DOCX file using python-docx.

    Args:
        file_path: Absolute or relative path to the DOCX file.

    Returns:
        Newline-separated paragraph text.
    """
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.error("Failed to extract text from DOCX '%s': %s", file_path, exc)
        raise


def extract_text_from_txt(file_path: str) -> str:
    """Read plain-text content from a .txt file.

    Args:
        file_path: Absolute or relative path to the text file.

    Returns:
        Raw file contents as a string.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception as exc:
        logger.error("Failed to read text file '%s': %s", file_path, exc)
        raise


def extract_text(file_path: str, file_type: str) -> str:
    """Dispatcher that routes extraction to the correct handler.

    Args:
        file_path: Path to the document file.
        file_type: MIME type or extension string.  Supported values include
            ``"pdf"``, ``"application/pdf"``, ``"docx"``,
            ``"application/vnd.openxmlformats-officedocument.wordprocessingml.document"``,
            ``"txt"``, ``"text/plain"``.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If *file_type* is not recognised.
    """
    normalized = file_type.lower()

    if "pdf" in normalized:
        return extract_text_from_pdf(file_path)
    elif "docx" in normalized or "wordprocessingml" in normalized:
        return extract_text_from_docx(file_path)
    elif "txt" in normalized or "plain" in normalized:
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: '{file_type}'")
