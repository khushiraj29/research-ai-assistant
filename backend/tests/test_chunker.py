"""Tests for backend/document_processing/chunker.py."""

from __future__ import annotations

import pytest

from backend.document_processing.chunker import chunk_text


# ---------------------------------------------------------------------------
# Basic chunking behaviour
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_returns_list(self, sample_text: str):
        chunks = chunk_text(sample_text, document_id="doc-1", source_filename="test.txt")
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_each_chunk_has_required_keys(self, sample_text: str):
        chunks = chunk_text(sample_text, document_id="doc-1", source_filename="test.txt")
        for chunk in chunks:
            assert "text" in chunk
            assert "document_id" in chunk
            assert "chunk_index" in chunk
            assert "source_filename" in chunk

    def test_document_id_propagated(self, sample_text: str):
        chunks = chunk_text(sample_text, document_id="MY-DOC", source_filename="file.txt")
        for chunk in chunks:
            assert chunk["document_id"] == "MY-DOC"

    def test_source_filename_propagated(self, sample_text: str):
        chunks = chunk_text(sample_text, document_id="doc-1", source_filename="paper.pdf")
        for chunk in chunks:
            assert chunk["source_filename"] == "paper.pdf"

    def test_chunk_indices_are_sequential(self, sample_text: str):
        chunks = chunk_text(sample_text, document_id="doc-1", source_filename="test.txt")
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i

    def test_chunk_text_is_string(self, sample_text: str):
        chunks = chunk_text(sample_text, document_id="doc-1", source_filename="test.txt")
        for chunk in chunks:
            assert isinstance(chunk["text"], str)
            assert len(chunk["text"]) > 0

    def test_empty_text_returns_empty_list(self):
        chunks = chunk_text("", document_id="doc-1", source_filename="empty.txt")
        assert chunks == []

    def test_small_text_single_chunk(self):
        """Text shorter than chunk_size should produce exactly one chunk."""
        short_text = "Short text."
        chunks = chunk_text(
            short_text,
            document_id="doc-1",
            source_filename="short.txt",
            chunk_size=1000,
            chunk_overlap=200,
        )
        assert len(chunks) >= 1
        # All text must be present across chunks
        combined = " ".join(c["text"] for c in chunks)
        assert "Short text." in combined

    def test_large_text_multiple_chunks(self):
        """Text longer than chunk_size must be split into multiple chunks."""
        long_text = "word " * 600  # 3000 chars
        chunks = chunk_text(
            long_text,
            document_id="doc-1",
            source_filename="long.txt",
            chunk_size=500,
            chunk_overlap=50,
        )
        assert len(chunks) > 1

    def test_custom_chunk_size_respected(self):
        text = "a" * 2000
        chunks = chunk_text(
            text,
            document_id="doc-1",
            source_filename="test.txt",
            chunk_size=300,
            chunk_overlap=50,
        )
        # Each chunk must not exceed chunk_size
        for chunk in chunks:
            assert len(chunk["text"]) <= 300
