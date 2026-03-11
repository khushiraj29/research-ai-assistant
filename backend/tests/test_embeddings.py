"""Tests for backend/embeddings/generator.py."""

from __future__ import annotations

import numpy as np
import pytest

from backend.embeddings.generator import EmbeddingGenerator


@pytest.fixture(scope="module")
def generator() -> EmbeddingGenerator:
    return EmbeddingGenerator(model_name="all-MiniLM-L6-v2")


class TestEmbeddingGenerator:
    def test_instantiation(self, generator: EmbeddingGenerator):
        assert generator.model_name == "all-MiniLM-L6-v2"
        assert generator.model is not None

    def test_single_embedding_is_list(self, generator: EmbeddingGenerator):
        emb = generator.generate_embedding("Hello world")
        assert isinstance(emb, list)

    def test_single_embedding_dimension(self, generator: EmbeddingGenerator):
        emb = generator.generate_embedding("Hello world")
        # Our stub always returns 384-dim vectors
        assert len(emb) == 384

    def test_single_embedding_values_are_floats(self, generator: EmbeddingGenerator):
        emb = generator.generate_embedding("test text")
        for val in emb:
            assert isinstance(val, float)

    def test_batch_embeddings_length(self, generator: EmbeddingGenerator):
        texts = ["first sentence", "second sentence", "third sentence"]
        embeddings = generator.generate_embeddings(texts)
        assert len(embeddings) == len(texts)

    def test_batch_each_embedding_dimension(self, generator: EmbeddingGenerator):
        texts = ["a", "b"]
        embeddings = generator.generate_embeddings(texts)
        for emb in embeddings:
            assert len(emb) == 384

    def test_empty_batch_returns_empty_list(self, generator: EmbeddingGenerator):
        embeddings = generator.generate_embeddings([])
        assert embeddings == []
