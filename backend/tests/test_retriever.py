"""Tests for backend/rag/retriever.py – FAISS-backed chunk store."""

from __future__ import annotations

import json
import os
from typing import List

import numpy as np
import pytest

from backend.rag.retriever import FAISSRetriever

DIM = 384  # matches our stub


def _make_chunks(n: int, doc_id: str = "doc-1") -> List[dict]:
    return [
        {
            "text": f"chunk text {i}",
            "document_id": doc_id,
            "chunk_index": i,
            "source_filename": "test.txt",
        }
        for i in range(n)
    ]


def _make_embeddings(n: int) -> List[List[float]]:
    return [np.zeros(DIM, dtype=np.float32).tolist() for _ in range(n)]


@pytest.fixture()
def retriever(tmp_path) -> FAISSRetriever:
    """Fresh retriever with a temp index path (no pre-existing index)."""
    return FAISSRetriever(index_path=str(tmp_path / "test_index"))


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestFAISSRetrieverInit:
    def test_starts_empty(self, retriever: FAISSRetriever):
        assert retriever.chunks == []
        # Index is None until first add
        assert retriever.index is None

    def test_index_path_stored(self, tmp_path):
        path = str(tmp_path / "myindex")
        r = FAISSRetriever(index_path=path)
        assert r.index_path == path


# ---------------------------------------------------------------------------
# Adding chunks
# ---------------------------------------------------------------------------


class TestAddChunks:
    def test_adds_chunks_to_list(self, retriever: FAISSRetriever):
        chunks = _make_chunks(3)
        embeddings = _make_embeddings(3)
        retriever.add_chunks(chunks, embeddings)
        assert len(retriever.chunks) == 3

    def test_index_created_after_add(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(2), _make_embeddings(2))
        assert retriever.index is not None

    def test_ntotal_matches_added_vectors(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(4), _make_embeddings(4))
        assert retriever.index.ntotal == 4

    def test_add_empty_is_noop(self, retriever: FAISSRetriever):
        retriever.add_chunks([], [])
        assert retriever.chunks == []
        assert retriever.index is None

    def test_cumulative_adds(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(2), _make_embeddings(2))
        retriever.add_chunks(_make_chunks(3, doc_id="doc-2"), _make_embeddings(3))
        assert len(retriever.chunks) == 5
        assert retriever.index.ntotal == 5


# ---------------------------------------------------------------------------
# Searching
# ---------------------------------------------------------------------------


class TestSearch:
    def test_returns_list(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(5), _make_embeddings(5))
        query = np.zeros(DIM, dtype=np.float32).tolist()
        results = retriever.search(query, top_k=3)
        assert isinstance(results, list)

    def test_result_count_respects_top_k(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(5), _make_embeddings(5))
        query = np.zeros(DIM, dtype=np.float32).tolist()
        results = retriever.search(query, top_k=3)
        assert len(results) <= 3

    def test_result_count_capped_by_index_size(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(2), _make_embeddings(2))
        query = np.zeros(DIM, dtype=np.float32).tolist()
        results = retriever.search(query, top_k=10)
        assert len(results) <= 2

    def test_results_contain_score(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(3), _make_embeddings(3))
        query = np.zeros(DIM, dtype=np.float32).tolist()
        results = retriever.search(query, top_k=2)
        for r in results:
            assert "score" in r
            assert isinstance(r["score"], float)

    def test_results_contain_chunk_keys(self, retriever: FAISSRetriever):
        retriever.add_chunks(_make_chunks(3), _make_embeddings(3))
        query = np.zeros(DIM, dtype=np.float32).tolist()
        results = retriever.search(query, top_k=2)
        for r in results:
            assert "text" in r
            assert "document_id" in r
            assert "chunk_index" in r
            assert "source_filename" in r

    def test_search_empty_index_returns_empty(self, retriever: FAISSRetriever):
        query = np.zeros(DIM, dtype=np.float32).tolist()
        results = retriever.search(query, top_k=5)
        assert results == []


# ---------------------------------------------------------------------------
# Persistence (save / load)
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_save_writes_metadata_json(self, retriever: FAISSRetriever, tmp_path):
        retriever.add_chunks(_make_chunks(3), _make_embeddings(3))
        retriever.save_index()

        meta_path = f"{retriever.index_path}_metadata.json"
        assert os.path.exists(meta_path)

        with open(meta_path, encoding="utf-8") as fh:
            saved = json.load(fh)
        assert len(saved) == 3

    def test_save_metadata_content(self, retriever: FAISSRetriever):
        chunks = _make_chunks(2)
        retriever.add_chunks(chunks, _make_embeddings(2))
        retriever.save_index()

        meta_path = f"{retriever.index_path}_metadata.json"
        with open(meta_path, encoding="utf-8") as fh:
            saved = json.load(fh)

        assert saved[0]["text"] == "chunk text 0"
        assert saved[0]["document_id"] == "doc-1"

    def test_save_on_empty_index_is_noop(self, retriever: FAISSRetriever):
        """save_index() should not raise or create files when index is None."""
        retriever.save_index()
        meta_path = f"{retriever.index_path}_metadata.json"
        # File should NOT be created
        assert not os.path.exists(meta_path)

    def test_load_index_reads_metadata(self, tmp_path):
        """Write metadata manually and verify load_index picks it up."""
        index_path = str(tmp_path / "load_test")
        # Write metadata file
        meta_path = f"{index_path}_metadata.json"
        chunks = _make_chunks(2)
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(chunks, fh)

        # Write a dummy .index file so os.path.exists check passes
        open(f"{index_path}.index", "w").close()

        r = FAISSRetriever(index_path=index_path)
        assert len(r.chunks) == 2
        assert r.chunks[0]["text"] == "chunk text 0"
