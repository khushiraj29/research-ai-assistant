"""Tests for all FastAPI route endpoints defined in backend/api/routes.py.

Uses FastAPI's TestClient (backed by httpx) and patches the orchestrator so
no ML models are loaded during tests.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app – conftest.py has already stubbed all heavy modules.
from backend.main import app

client = TestClient(app, raise_server_exceptions=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_QUESTION_RESULT: dict[str, Any] = {
    "answer": "Artificial intelligence enables computers to learn.",
    "sources": [
        {
            "document_id": "doc-abc",
            "source_filename": "paper.txt",
            "chunk_index": 0,
            "score": 0.25,
        }
    ],
    "model_used": "gpt-3.5-turbo",
}

_MOCK_SUMMARY_RESULT: dict[str, Any] = {
    "document_id": "doc-abc",
    "summary": "This paper covers AI and machine learning topics.",
    "length": "medium",
}

_MOCK_GRAPH_RESULT: dict[str, Any] = {
    "document_id": "doc-abc",
    "nodes": [{"id": "AI", "label": "AI", "entity_type": "ORG", "document_id": "doc-abc"}],
    "edges": [{"source": "AI", "target": "ML", "relationship": "CO_OCCURS_WITH"}],
}

_MOCK_PROCESS_RESULT: dict[str, Any] = {
    "document_id": "doc-abc",
    "chunk_count": 5,
    "status": "success",
}


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_body_shape(self):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "version" in data


# ---------------------------------------------------------------------------
# POST /upload-document
# ---------------------------------------------------------------------------


class TestUploadDocument:
    def test_upload_txt_returns_200(self, tmp_path):
        p = tmp_path / "research.txt"
        p.write_text("Sample research text.")
        with patch("backend.api.routes.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path / "uploads")
            with open(str(p), "rb") as fh:
                resp = client.post(
                    "/upload-document",
                    files={"file": ("research.txt", fh, "text/plain")},
                )
        assert resp.status_code == 200

    def test_upload_returns_doc_id(self, tmp_path):
        p = tmp_path / "doc.txt"
        p.write_text("Content.")
        with patch("backend.api.routes.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path / "uploads")
            with open(str(p), "rb") as fh:
                resp = client.post(
                    "/upload-document",
                    files={"file": ("doc.txt", fh, "text/plain")},
                )
        data = resp.json()
        assert "doc_id" in data
        assert len(data["doc_id"]) > 0

    def test_upload_returns_filename(self, tmp_path):
        p = tmp_path / "paper.txt"
        p.write_text("Text.")
        with patch("backend.api.routes.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path / "uploads")
            with open(str(p), "rb") as fh:
                resp = client.post(
                    "/upload-document",
                    files={"file": ("paper.txt", fh, "text/plain")},
                )
        data = resp.json()
        assert data["filename"] == "paper.txt"

    def test_upload_unsupported_extension_returns_400(self):
        resp = client.post(
            "/upload-document",
            files={"file": ("file.xyz", b"data", "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_upload_no_file_returns_422(self):
        resp = client.post("/upload-document")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /process-document
# ---------------------------------------------------------------------------


class TestProcessDocument:
    def test_process_returns_200(self, tmp_path):
        with patch("backend.api.routes.orchestrator") as mock_orch, \
             patch("backend.api.routes.settings") as mock_settings:
            # Simulate a pre-uploaded file
            upload_dir = tmp_path / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            fake_file = upload_dir / "doc-abc.txt"
            fake_file.write_text("Content.")
            mock_settings.UPLOAD_DIR = str(upload_dir)
            mock_orch.process_document.return_value = _MOCK_PROCESS_RESULT

            resp = client.post("/process-document", json={"document_id": "doc-abc"})
        assert resp.status_code == 200

    def test_process_returns_chunk_count(self, tmp_path):
        with patch("backend.api.routes.orchestrator") as mock_orch, \
             patch("backend.api.routes.settings") as mock_settings:
            upload_dir = tmp_path / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            (upload_dir / "doc-abc.txt").write_text("Content.")
            mock_settings.UPLOAD_DIR = str(upload_dir)
            mock_orch.process_document.return_value = _MOCK_PROCESS_RESULT

            resp = client.post("/process-document", json={"document_id": "doc-abc"})
        assert resp.json()["chunk_count"] == 5

    def test_process_missing_doc_returns_404(self, tmp_path):
        with patch("backend.api.routes.settings") as mock_settings:
            upload_dir = tmp_path / "empty_uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            mock_settings.UPLOAD_DIR = str(upload_dir)

            resp = client.post("/process-document", json={"document_id": "nonexistent"})
        assert resp.status_code == 404

    def test_process_missing_body_returns_422(self):
        resp = client.post("/process-document", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /ask-question
# ---------------------------------------------------------------------------


class TestAskQuestion:
    def test_returns_200(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.answer_question.return_value = _MOCK_QUESTION_RESULT
            resp = client.post("/ask-question", json={"question": "What is AI?"})
        assert resp.status_code == 200

    def test_response_has_answer(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.answer_question.return_value = _MOCK_QUESTION_RESULT
            resp = client.post("/ask-question", json={"question": "What is AI?"})
        assert resp.json()["answer"] == _MOCK_QUESTION_RESULT["answer"]

    def test_response_has_sources(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.answer_question.return_value = _MOCK_QUESTION_RESULT
            resp = client.post("/ask-question", json={"question": "What is AI?"})
        assert isinstance(resp.json()["sources"], list)

    def test_response_has_model_used(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.answer_question.return_value = _MOCK_QUESTION_RESULT
            resp = client.post("/ask-question", json={"question": "What is AI?"})
        assert "model_used" in resp.json()

    def test_custom_top_k_forwarded(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.answer_question.return_value = _MOCK_QUESTION_RESULT
            client.post("/ask-question", json={"question": "test", "top_k": 3})
            mock_orch.answer_question.assert_called_once_with(question="test", top_k=3)

    def test_invalid_top_k_returns_422(self):
        resp = client.post("/ask-question", json={"question": "test", "top_k": 0})
        assert resp.status_code == 422

    def test_missing_question_returns_422(self):
        resp = client.post("/ask-question", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /summarize-document
# ---------------------------------------------------------------------------


class TestSummarizeDocument:
    def test_returns_200(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.summarize_document.return_value = _MOCK_SUMMARY_RESULT
            resp = client.post(
                "/summarize-document",
                json={"document_id": "doc-abc", "length": "medium"},
            )
        assert resp.status_code == 200

    def test_response_has_summary(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.summarize_document.return_value = _MOCK_SUMMARY_RESULT
            resp = client.post(
                "/summarize-document",
                json={"document_id": "doc-abc"},
            )
        assert "summary" in resp.json()

    def test_invalid_length_returns_422(self):
        resp = client.post(
            "/summarize-document",
            json={"document_id": "doc-abc", "length": "super-long"},
        )
        assert resp.status_code == 422

    def test_all_valid_lengths_accepted(self):
        for length in ("short", "medium", "detailed"):
            with patch("backend.api.routes.orchestrator") as mock_orch:
                mock_orch.summarize_document.return_value = {**_MOCK_SUMMARY_RESULT, "length": length}
                resp = client.post(
                    "/summarize-document",
                    json={"document_id": "doc-abc", "length": length},
                )
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /generate-knowledge-graph
# ---------------------------------------------------------------------------


class TestGenerateKnowledgeGraph:
    def test_returns_200(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.generate_knowledge_graph.return_value = _MOCK_GRAPH_RESULT
            resp = client.post(
                "/generate-knowledge-graph",
                json={"document_id": "doc-abc"},
            )
        assert resp.status_code == 200

    def test_response_has_nodes_and_edges(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.generate_knowledge_graph.return_value = _MOCK_GRAPH_RESULT
            resp = client.post(
                "/generate-knowledge-graph",
                json={"document_id": "doc-abc"},
            )
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert "node_count" in data
        assert "edge_count" in data

    def test_node_count_matches_nodes_length(self):
        with patch("backend.api.routes.orchestrator") as mock_orch:
            mock_orch.generate_knowledge_graph.return_value = _MOCK_GRAPH_RESULT
            resp = client.post(
                "/generate-knowledge-graph",
                json={"document_id": "doc-abc"},
            )
        data = resp.json()
        assert data["node_count"] == len(data["nodes"])

    def test_missing_document_id_returns_422(self):
        resp = client.post("/generate-knowledge-graph", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /knowledge-graph
# ---------------------------------------------------------------------------


class TestGetKnowledgeGraph:
    def test_returns_200_without_doc_id(self):
        with patch("backend.api.routes.orchestrator") as _mock_orch, \
             patch("backend.knowledge_graph.neo4j_client.Neo4jClient", side_effect=Exception("no neo4j")):
            resp = client.get("/knowledge-graph")
        assert resp.status_code == 200

    def test_returns_200_with_doc_id(self):
        with patch("backend.api.routes.orchestrator") as mock_orch, \
             patch("backend.knowledge_graph.neo4j_client.Neo4jClient", side_effect=Exception("no neo4j")):
            mock_orch.generate_knowledge_graph.return_value = _MOCK_GRAPH_RESULT
            resp = client.get("/knowledge-graph", params={"document_id": "doc-abc"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /documents
# ---------------------------------------------------------------------------


class TestListDocuments:
    def test_empty_directory_returns_empty_list(self, tmp_path):
        with patch("backend.api.routes.settings") as mock_settings:
            upload_dir = tmp_path / "uploads"
            upload_dir.mkdir()
            mock_settings.UPLOAD_DIR = str(upload_dir)
            resp = client.get("/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_uploaded_files_appear_in_list(self, tmp_path):
        with patch("backend.api.routes.settings") as mock_settings:
            upload_dir = tmp_path / "uploads"
            upload_dir.mkdir()
            (upload_dir / "abc123.txt").write_text("content")
            mock_settings.UPLOAD_DIR = str(upload_dir)
            resp = client.get("/documents")
        data = resp.json()
        assert resp.status_code == 200
        assert len(data) == 1
        assert "document_id" in data[0]
        assert "filename" in data[0]

    def test_nonexistent_directory_returns_empty_list(self, tmp_path):
        with patch("backend.api.routes.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path / "does_not_exist")
            resp = client.get("/documents")
        assert resp.status_code == 200
        assert resp.json() == []
