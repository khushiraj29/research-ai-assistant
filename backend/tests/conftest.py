"""
conftest.py – shared pytest fixtures and sys.modules stubs.

All heavy ML/DB dependencies (langchain, sentence-transformers, faiss, spacy,
openai, neo4j, PyMuPDF, python-docx) are replaced with lightweight stubs
*before* any application module is imported.  This lets the entire backend
test suite run on a plain Python environment that only has the packages listed
in requirements-test.txt.
"""

from __future__ import annotations

import os
import sys
import types
from typing import Any, List
from unittest.mock import MagicMock

import numpy as np

# ---------------------------------------------------------------------------
# Helper: create a real module object (not MagicMock) so sub-attribute access
# works predictably when Python resolves package hierarchies.
# ---------------------------------------------------------------------------


def _make_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ===========================================================================
# LangChain stubs
# ===========================================================================

# --- RecursiveCharacterTextSplitter -----------------------------------------


class _RecursiveCharacterTextSplitter:
    """Minimal stub: splits on chunk_size boundaries with overlap."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Any = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        step = max(1, self.chunk_size - self.chunk_overlap)
        chunks = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks


# --- PromptTemplate ----------------------------------------------------------


class _PromptTemplate:
    def __init__(self, input_variables: List[str] = (), template: str = "") -> None:
        self.input_variables = list(input_variables)
        self.template = template

    def format(self, **kwargs: Any) -> str:
        result = self.template
        for key, value in kwargs.items():
            result = result.replace("{" + key + "}", str(value))
        return result


# Register langchain sub-modules
_lc = _make_module("langchain")
_lc_ts = _make_module("langchain.text_splitter")
_lc_ts.RecursiveCharacterTextSplitter = _RecursiveCharacterTextSplitter  # type: ignore[attr-defined]

_lc_prompts = _make_module("langchain.prompts")
_lc_prompts.PromptTemplate = _PromptTemplate  # type: ignore[attr-defined]

_make_module("langchain.chains")
_make_module("langchain.schema")
_make_module("langchain_community")
_make_module("langchain_community.vectorstores")

# --- langchain_openai -------------------------------------------------------


class _ChatOpenAI:
    """Stub that returns a predictable mocked AI response."""

    def __init__(self, model: str = "gpt-3.5-turbo", openai_api_key: str = "", temperature: float = 0.2) -> None:
        self.model = model

    def invoke(self, prompt: str) -> Any:
        _msg = MagicMock()
        _msg.content = f"[MOCK ANSWER] {prompt[:60]}..."
        return _msg


_lc_openai = _make_module("langchain_openai")
_lc_openai.ChatOpenAI = _ChatOpenAI  # type: ignore[attr-defined]

# ===========================================================================
# sentence-transformers stub
# ===========================================================================


class _SentenceTransformer:
    """Returns deterministic random-ish embeddings (seeded on model name)."""

    DIMENSION = 384

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    def encode(
        self,
        texts: Any,
        convert_to_numpy: bool = True,
        batch_size: int = 32,
    ) -> np.ndarray:
        if isinstance(texts, str):
            return np.zeros(self.DIMENSION, dtype=np.float32)
        return np.zeros((len(texts), self.DIMENSION), dtype=np.float32)


_st = _make_module("sentence_transformers")
_st.SentenceTransformer = _SentenceTransformer  # type: ignore[attr-defined]

# ===========================================================================
# FAISS stub
# ===========================================================================


class _FAISSIndex:
    """Minimal in-memory L2 index stub."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self._vectors: List[np.ndarray] = []
        self.ntotal: int = 0

    def add(self, vectors: np.ndarray) -> None:
        for v in vectors:
            self._vectors.append(v.copy())
        self.ntotal = len(self._vectors)

    def search(
        self, query: np.ndarray, k: int
    ):
        k = min(k, self.ntotal)
        if k == 0:
            return np.array([[]], dtype=np.float32), np.array([[-1]], dtype=np.int64)
        distances = np.full((1, k), 0.5, dtype=np.float32)
        indices = np.arange(k, dtype=np.int64).reshape(1, k)
        return distances, indices


def _faiss_write_index(index: Any, path: str) -> None:
    """No-op: real write is tested via metadata JSON, not the binary index."""


def _faiss_read_index(path: str) -> _FAISSIndex:
    idx = _FAISSIndex(dimension=384)
    idx.ntotal = 0
    return idx


_faiss = _make_module("faiss")
_faiss.IndexFlatL2 = _FAISSIndex  # type: ignore[attr-defined]
_faiss.write_index = _faiss_write_index  # type: ignore[attr-defined]
_faiss.read_index = _faiss_read_index  # type: ignore[attr-defined]

# ===========================================================================
# spaCy stub
# ===========================================================================


def _spacy_load(model_name: str) -> MagicMock:
    """Return a callable MagicMock that produces a MagicMock doc."""
    nlp = MagicMock(name=f"spacy_model[{model_name}]")
    doc = MagicMock(name="spacy_doc")
    doc.ents = []
    doc.sents = []
    nlp.return_value = doc
    return nlp


_spacy = _make_module("spacy")
_spacy.load = _spacy_load  # type: ignore[attr-defined]

# ===========================================================================
# Neo4j stub
# ===========================================================================

_neo4j = _make_module("neo4j")
_neo4j.GraphDatabase = MagicMock()  # type: ignore[attr-defined]

# ===========================================================================
# OpenAI stub (direct client – only needed if imported directly)
# ===========================================================================

_make_module("openai")

# ===========================================================================
# PyMuPDF (fitz) stub
# ===========================================================================

_fitz = _make_module("fitz")
_fitz.open = MagicMock()  # type: ignore[attr-defined]

# ===========================================================================
# python-docx stub
# ===========================================================================

_docx = _make_module("docx")
_docx.Document = MagicMock()  # type: ignore[attr-defined]

# ===========================================================================
# aiofiles stub (not installed in test env)
# ===========================================================================

_aiofiles = _make_module("aiofiles")

# Provide a minimal async context-manager so `async with aiofiles.open(...)` works.
import asyncio  # noqa: E402


class _AsyncFile:
    async def write(self, data: bytes) -> None:  # noqa: D401
        pass

    async def read(self) -> bytes:
        return b""

    async def __aenter__(self) -> "_AsyncFile":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


def _aiofiles_open(path: str, mode: str = "rb", **kwargs: Any) -> "_AsyncFile":
    return _AsyncFile()


_aiofiles.open = _aiofiles_open  # type: ignore[attr-defined]

# ===========================================================================
# Shared pytest fixtures
# ===========================================================================

import pytest  # noqa: E402


@pytest.fixture()
def sample_text() -> str:
    return (
        "Artificial intelligence (AI) is a branch of computer science. "
        "Machine learning is a subset of AI. "
        "Deep learning uses neural networks. "
        "Natural language processing enables machines to understand text. "
        "Computer vision allows machines to interpret images. "
        "Reinforcement learning trains agents through rewards and penalties."
    )


@pytest.fixture()
def txt_file(tmp_path: Any, sample_text: str):
    """A temporary .txt file containing sample_text."""
    p = tmp_path / "sample.txt"
    p.write_text(sample_text, encoding="utf-8")
    return str(p)
