"""Document orchestrator: coordinates all AI pipeline stages for a given document."""

import logging
import os
from typing import Dict, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from backend.document_processing.chunker import chunk_text
from backend.document_processing.extractor import extract_text
from backend.embeddings.generator import EmbeddingGenerator
from backend.knowledge_graph.extractor import KnowledgeGraphExtractor
from backend.rag.pipeline import RAGPipeline
from backend.rag.retriever import FAISSRetriever
from backend.utils.config import settings

logger = logging.getLogger(__name__)

# Summarization prompt templates per length variant
_SUMMARY_PROMPTS: Dict[str, str] = {
    "short": (
        "Summarize the following research document in 2-3 sentences, "
        "capturing the core topic and main finding.\n\nDocument:\n{text}\n\nSummary:"
    ),
    "medium": (
        "Write a clear, well-structured summary of the following research "
        "document in one paragraph (6-8 sentences). Cover the main objectives, "
        "methods, and conclusions.\n\nDocument:\n{text}\n\nSummary:"
    ),
    "detailed": (
        "Provide a detailed summary of the following research document, "
        "organized into three sections: (1) Background & Objectives, "
        "(2) Methods & Findings, (3) Conclusions & Implications. "
        "Use 3-5 sentences per section.\n\nDocument:\n{text}\n\nDetailed Summary:"
    ),
}


class DocumentOrchestrator:
    """High-level orchestration layer that ties together extraction, embedding,
    retrieval, summarization, and knowledge-graph generation.

    All heavy objects (models, indexes) are lazily initialised on first use so
    that the class can be instantiated cheaply inside the FastAPI app startup.
    """

    def __init__(self) -> None:
        self._embedding_generator: Optional[EmbeddingGenerator] = None
        self._retriever: Optional[FAISSRetriever] = None
        self._rag_pipeline: Optional[RAGPipeline] = None
        self._kg_extractor: Optional[KnowledgeGraphExtractor] = None
        self._llm: Optional[ChatOpenAI] = None

    # ------------------------------------------------------------------
    # Lazy-initialised components
    # ------------------------------------------------------------------

    @property
    def embedding_generator(self) -> EmbeddingGenerator:
        if self._embedding_generator is None:
            self._embedding_generator = EmbeddingGenerator(settings.EMBEDDING_MODEL)
        return self._embedding_generator

    @property
    def retriever(self) -> FAISSRetriever:
        if self._retriever is None:
            self._retriever = FAISSRetriever(settings.FAISS_INDEX_PATH)
        return self._retriever

    @property
    def rag_pipeline(self) -> RAGPipeline:
        if self._rag_pipeline is None:
            self._rag_pipeline = RAGPipeline()
        return self._rag_pipeline

    @property
    def kg_extractor(self) -> KnowledgeGraphExtractor:
        if self._kg_extractor is None:
            self._kg_extractor = KnowledgeGraphExtractor()
        return self._kg_extractor

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.3,
            )
        return self._llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_document(
        self, document_id: str, file_path: str, filename: str
    ) -> Dict:
        """Extract, chunk, embed, and index a document.

        Args:
            document_id: Unique identifier assigned at upload time.
            file_path: Absolute path to the saved file.
            filename: Original filename (used to determine file type).

        Returns:
            Dict with ``document_id``, ``chunk_count``, and ``status``.
        """
        # Determine file type from extension
        ext = os.path.splitext(filename)[1].lstrip(".").lower()
        file_type_map = {"pdf": "pdf", "docx": "docx", "txt": "txt"}
        file_type = file_type_map.get(ext, "txt")

        logger.info("Processing document '%s' (type=%s).", document_id, file_type)

        # 1. Extract raw text
        text = extract_text(file_path, file_type)

        # 2. Split into overlapping chunks
        chunks = chunk_text(
            text=text,
            document_id=document_id,
            source_filename=filename,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        # 3. Generate embeddings for all chunks in a single batch
        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_generator.generate_embeddings(texts)

        # 4. Add to FAISS index and persist
        self.retriever.add_chunks(chunks, embeddings)
        self.retriever.save_index()

        logger.info(
            "Document '%s' processed: %d chunks indexed.", document_id, len(chunks)
        )
        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "status": "success",
        }

    def answer_question(self, question: str, top_k: int = 5) -> Dict:
        """Delegate question-answering to the RAG pipeline.

        Args:
            question: Natural-language question from the user.
            top_k: Number of context chunks to retrieve.

        Returns:
            Dict from :meth:`~backend.rag.pipeline.RAGPipeline.query`.
        """
        return self.rag_pipeline.query(question, top_k=top_k)

    def summarize_document(self, document_id: str, length: str = "medium") -> Dict:
        """Generate a summary of a previously processed document.

        The method reconstructs the document text from the FAISS chunk store so
        that no separate raw-text store is required.

        Args:
            document_id: The document to summarize.
            length: One of ``"short"``, ``"medium"``, or ``"detailed"``.

        Returns:
            Dict with ``document_id``, ``summary``, and ``length``.
        """
        # Collect all chunks that belong to this document from the FAISS store
        all_chunks = self.retriever.chunks
        doc_chunks = sorted(
            [c for c in all_chunks if c.get("document_id") == document_id],
            key=lambda c: c.get("chunk_index", 0),
        )

        if not doc_chunks:
            return {
                "document_id": document_id,
                "summary": "Document not found or has not been processed yet.",
                "length": length,
            }

        # Reconstruct approximate full text (may have minor overlap artefacts)
        full_text = "\n\n".join(c["text"] for c in doc_chunks)

        # Truncate to avoid exceeding context window
        truncated_text = full_text[: settings.SUMMARY_MAX_CHARS]

        prompt_template = _SUMMARY_PROMPTS.get(length, _SUMMARY_PROMPTS["medium"])
        prompt = PromptTemplate(input_variables=["text"], template=prompt_template)
        formatted = prompt.format(text=truncated_text)

        response = self.llm.invoke(formatted)
        summary: str = response.content if hasattr(response, "content") else str(response)

        return {"document_id": document_id, "summary": summary, "length": length}

    def generate_knowledge_graph(self, document_id: str) -> Dict:
        """Extract entities and relationships and optionally store in Neo4j.

        Args:
            document_id: The document whose text should be analysed.

        Returns:
            Graph dict with ``nodes``, ``edges``, and ``document_id``.
        """
        # Reconstruct text from indexed chunks
        all_chunks = self.retriever.chunks
        doc_chunks = sorted(
            [c for c in all_chunks if c.get("document_id") == document_id],
            key=lambda c: c.get("chunk_index", 0),
        )

        if not doc_chunks:
            return {
                "nodes": [],
                "edges": [],
                "document_id": document_id,
            }

        full_text = "\n\n".join(c["text"] for c in doc_chunks)

        # Build graph in-memory
        graph_data = self.kg_extractor.build_graph(full_text, document_id)

        # Attempt to persist to Neo4j; gracefully degrade if unavailable
        try:
            from backend.knowledge_graph.neo4j_client import Neo4jClient

            neo4j = Neo4jClient(
                uri=settings.NEO4J_URI,
                user=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
            )
            neo4j.store_graph(graph_data)
            neo4j.close()
        except Exception as exc:
            logger.warning(
                "Neo4j unavailable; graph data will not be persisted. Error: %s", exc
            )

        return graph_data
