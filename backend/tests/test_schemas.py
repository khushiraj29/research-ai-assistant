"""Tests for backend/api/schemas.py – Pydantic model validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.api.schemas import (
    DocumentInfo,
    DocumentUploadResponse,
    HealthResponse,
    KnowledgeGraphRequest,
    KnowledgeGraphResponse,
    ProcessDocumentRequest,
    ProcessDocumentResponse,
    QuestionRequest,
    QuestionResponse,
    SummarizeRequest,
    SummarizeResponse,
)


# ---------------------------------------------------------------------------
# DocumentUploadResponse
# ---------------------------------------------------------------------------


class TestDocumentUploadResponse:
    def test_valid_creation(self):
        resp = DocumentUploadResponse(
            doc_id="abc-123",
            filename="paper.pdf",
            file_type="pdf",
            file_size=1024,
            message="Uploaded successfully.",
        )
        assert resp.doc_id == "abc-123"
        assert resp.filename == "paper.pdf"
        assert resp.file_type == "pdf"
        assert resp.file_size == 1024

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            DocumentUploadResponse(
                doc_id="abc-123",
                filename="paper.pdf",
                file_type="pdf",
                # file_size missing
                message="ok",
            )


# ---------------------------------------------------------------------------
# ProcessDocumentRequest / Response
# ---------------------------------------------------------------------------


class TestProcessDocumentRequest:
    def test_valid(self):
        req = ProcessDocumentRequest(document_id="doc-xyz")
        assert req.document_id == "doc-xyz"

    def test_empty_id_is_allowed(self):
        req = ProcessDocumentRequest(document_id="")
        assert req.document_id == ""


class TestProcessDocumentResponse:
    def test_valid(self):
        resp = ProcessDocumentResponse(
            document_id="doc-xyz",
            status="success",
            chunk_count=10,
            message="Processed 10 chunks.",
        )
        assert resp.chunk_count == 10
        assert resp.status == "success"


# ---------------------------------------------------------------------------
# QuestionRequest / Response
# ---------------------------------------------------------------------------


class TestQuestionRequest:
    def test_default_top_k(self):
        req = QuestionRequest(question="What is AI?")
        assert req.top_k == 5

    def test_custom_top_k(self):
        req = QuestionRequest(question="What is AI?", top_k=3)
        assert req.top_k == 3

    def test_top_k_below_min_raises(self):
        with pytest.raises(ValidationError):
            QuestionRequest(question="test", top_k=0)

    def test_top_k_above_max_raises(self):
        with pytest.raises(ValidationError):
            QuestionRequest(question="test", top_k=21)

    def test_missing_question_raises(self):
        with pytest.raises(ValidationError):
            QuestionRequest()


class TestQuestionResponse:
    def test_valid_no_sources(self):
        resp = QuestionResponse(
            answer="This is the answer.",
            sources=[],
            model_used="gpt-3.5-turbo",
        )
        assert resp.answer == "This is the answer."
        assert resp.sources == []

    def test_valid_with_sources(self):
        resp = QuestionResponse(
            answer="Answer",
            sources=[{"document_id": "doc-1", "source_filename": "paper.pdf", "chunk_index": 0, "score": 0.4}],
            model_used="gpt-3.5-turbo",
        )
        assert len(resp.sources) == 1


# ---------------------------------------------------------------------------
# SummarizeRequest / Response
# ---------------------------------------------------------------------------


class TestSummarizeRequest:
    def test_default_length(self):
        req = SummarizeRequest(document_id="doc-1")
        assert req.length == "medium"

    def test_valid_lengths(self):
        for length in ("short", "medium", "detailed"):
            req = SummarizeRequest(document_id="doc-1", length=length)
            assert req.length == length

    def test_invalid_length_raises(self):
        with pytest.raises(ValidationError):
            SummarizeRequest(document_id="doc-1", length="tldr")


class TestSummarizeResponse:
    def test_valid(self):
        resp = SummarizeResponse(document_id="doc-1", summary="A short summary.", length="short")
        assert resp.summary == "A short summary."


# ---------------------------------------------------------------------------
# KnowledgeGraphRequest / Response
# ---------------------------------------------------------------------------


class TestKnowledgeGraphRequest:
    def test_valid(self):
        req = KnowledgeGraphRequest(document_id="doc-1")
        assert req.document_id == "doc-1"


class TestKnowledgeGraphResponse:
    def test_valid_empty_graph(self):
        resp = KnowledgeGraphResponse(
            document_id="doc-1",
            nodes=[],
            edges=[],
            node_count=0,
            edge_count=0,
        )
        assert resp.node_count == 0
        assert resp.edge_count == 0

    def test_valid_with_data(self):
        nodes = [{"id": "AI", "label": "AI", "entity_type": "ORG"}]
        edges = [{"source": "AI", "target": "ML", "relationship": "CO_OCCURS_WITH"}]
        resp = KnowledgeGraphResponse(
            document_id="doc-1",
            nodes=nodes,
            edges=edges,
            node_count=1,
            edge_count=1,
        )
        assert resp.node_count == 1
        assert resp.edge_count == 1


# ---------------------------------------------------------------------------
# DocumentInfo
# ---------------------------------------------------------------------------


class TestDocumentInfo:
    def test_valid(self):
        info = DocumentInfo(
            document_id="doc-1",
            filename="paper.pdf",
            file_type="pdf",
            file_size=2048,
            uploaded_at="2024-01-01T00:00:00",
        )
        assert info.file_size == 2048


# ---------------------------------------------------------------------------
# HealthResponse
# ---------------------------------------------------------------------------


class TestHealthResponse:
    def test_valid(self):
        resp = HealthResponse(status="healthy", message="OK", version="0.1.0")
        assert resp.status == "healthy"
        assert resp.version == "0.1.0"
