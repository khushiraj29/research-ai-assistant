"""FAISS-based vector store for similarity search over document chunks."""

import json
import logging
import os
from typing import Dict, List, Optional

import faiss
import numpy as np

logger = logging.getLogger(__name__)

# Metadata sidecar file lives next to the FAISS index binary
_METADATA_SUFFIX = "_metadata.json"


class FAISSRetriever:
    """Manages a FAISS flat L2 index for storing and querying chunk embeddings.

    The index binary and a companion JSON metadata file are persisted together
    on disk so that the retriever survives application restarts.

    Attributes:
        index_path: Filesystem path (without extension) where the index is saved.
        index: The underlying FAISS index object.
        chunks: List of chunk dicts stored in insertion order, parallel to the
                index vectors.
    """

    def __init__(self, index_path: Optional[str] = None) -> None:
        """Initialise the retriever and optionally load an existing index.

        Args:
            index_path: Path (without file extension) to persist the FAISS
                index and metadata.  Defaults to ``"./database/faiss_index"``.
        """
        from backend.utils.config import settings

        self.index_path: str = index_path or settings.FAISS_INDEX_PATH
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Dict] = []

        if os.path.exists(f"{self.index_path}.index"):
            self.load_index()
        else:
            logger.info("No existing FAISS index found; starting fresh.")

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def _ensure_index(self, dimension: int) -> None:
        """Create a new flat L2 index if one does not exist yet.

        Args:
            dimension: Embedding dimensionality (must match all future vectors).
        """
        if self.index is None:
            self.index = faiss.IndexFlatL2(dimension)
            logger.info("Created new FAISS index with dimension %d.", dimension)

    def add_chunks(self, chunks: List[Dict], embeddings: List[List[float]]) -> None:
        """Add document chunks and their embeddings to the index.

        Args:
            chunks: Chunk metadata dicts (text, document_id, chunk_index, …).
            embeddings: Corresponding embedding vectors; must be same length as
                        *chunks*.
        """
        if not chunks:
            return

        vectors = np.array(embeddings, dtype=np.float32)
        dimension = vectors.shape[1]
        self._ensure_index(dimension)

        self.index.add(vectors)  # type: ignore[union-attr]
        self.chunks.extend(chunks)
        logger.info("Added %d chunks to FAISS index (total: %d).", len(chunks), len(self.chunks))

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Find the *top_k* most similar chunks to *query_embedding*.

        Args:
            query_embedding: Dense query vector produced by the same embedding
                             model used to index the chunks.
            top_k: Maximum number of results to return.

        Returns:
            A list of result dicts, each containing all keys from the original
            chunk dict plus a ``score`` key (lower L2 distance = more similar).
            Returns an empty list when the index is empty.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index is empty; returning no results.")
            return []

        query_vector = np.array([query_embedding], dtype=np.float32)
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, k)

        results: List[Dict] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                # FAISS returns -1 when fewer than k results are available
                continue
            chunk = dict(self.chunks[idx])
            chunk["score"] = float(dist)
            results.append(chunk)

        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_index(self) -> None:
        """Persist the FAISS index binary and chunk metadata to disk."""
        if self.index is None:
            logger.warning("Nothing to save – index is uninitialised.")
            return

        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        index_file = f"{self.index_path}.index"
        meta_file = f"{self.index_path}{_METADATA_SUFFIX}"

        faiss.write_index(self.index, index_file)
        with open(meta_file, "w", encoding="utf-8") as fh:
            json.dump(self.chunks, fh, ensure_ascii=False, indent=2)

        logger.info("FAISS index saved to '%s'.", index_file)

    def load_index(self) -> None:
        """Load the FAISS index binary and chunk metadata from disk."""
        index_file = f"{self.index_path}.index"
        meta_file = f"{self.index_path}{_METADATA_SUFFIX}"

        if not os.path.exists(index_file):
            raise FileNotFoundError(f"FAISS index not found at '{index_file}'.")

        self.index = faiss.read_index(index_file)
        logger.info("Loaded FAISS index with %d vectors.", self.index.ntotal)

        if os.path.exists(meta_file):
            with open(meta_file, "r", encoding="utf-8") as fh:
                self.chunks = json.load(fh)
            logger.info("Loaded %d chunk metadata records.", len(self.chunks))
        else:
            logger.warning("Metadata file '%s' not found; chunk info will be empty.", meta_file)
            self.chunks = []
