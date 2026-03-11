"""Embedding generation using sentence-transformers."""

import logging
from typing import List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Wraps a sentence-transformers model for text embedding generation.

    Attributes:
        model_name: HuggingFace model identifier (e.g. "all-MiniLM-L6-v2").
        model: Loaded SentenceTransformer instance.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Load the sentence-transformers model.

        Args:
            model_name: Name of the pre-trained model to load.
        """
        self.model_name = model_name
        logger.info("Loading embedding model: %s", model_name)
        self.model: SentenceTransformer = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully.")

    def generate_embedding(self, text: str) -> List[float]:
        """Encode a single text string into a dense embedding vector.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch of texts into embedding vectors.

        Batching is significantly faster than calling :meth:`generate_embedding`
        in a loop because the underlying model can process the batch in parallel
        on GPU/CPU via the sentence-transformers library.

        Args:
            texts: List of input strings to embed.

        Returns:
            A list of embedding vectors, one per input text.
        """
        logger.info("Generating embeddings for %d texts.", len(texts))
        embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
        return [emb.tolist() for emb in embeddings]
