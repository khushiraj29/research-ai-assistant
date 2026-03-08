"""Text chunking utilities using LangChain's RecursiveCharacterTextSplitter."""

import logging
from typing import Dict, List

from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    document_id: str,
    source_filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Dict]:
    """Split *text* into overlapping chunks suitable for embedding and retrieval.

    Args:
        text: The full document text to split.
        document_id: Unique identifier of the parent document.
        source_filename: Original filename of the document.
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        A list of chunk dicts, each containing:
            - ``text``: The chunk's text content.
            - ``document_id``: The parent document's ID.
            - ``chunk_index``: Zero-based position of the chunk in the sequence.
            - ``source_filename``: Original filename for citation purposes.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Prefer splitting on paragraph/sentence boundaries before characters
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks: List[str] = splitter.split_text(text)
    logger.info(
        "Document '%s' split into %d chunks (size=%d, overlap=%d)",
        document_id,
        len(raw_chunks),
        chunk_size,
        chunk_overlap,
    )

    return [
        {
            "text": chunk,
            "document_id": document_id,
            "chunk_index": idx,
            "source_filename": source_filename,
        }
        for idx, chunk in enumerate(raw_chunks)
    ]
