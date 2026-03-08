"""FastAPI route definitions for the Research AI Assistant backend."""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

import aiofiles
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

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
from backend.services.orchestrator import DocumentOrchestrator
from backend.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Single orchestrator instance shared across all requests
orchestrator = DocumentOrchestrator()

# Allowed upload extensions
_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(
        status="healthy",
        message="Research AI Assistant backend is running.",
        version="0.1.0",
    )


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@router.post("/upload-document", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Accept a multipart file upload and save it to the uploads directory.

    Supported file types: PDF, DOCX, TXT.
    """
    try:
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Allowed: {_ALLOWED_EXTENSIONS}",
            )

        # Generate a unique document ID and derive the save path
        doc_id = str(uuid.uuid4())
        save_dir = settings.UPLOAD_DIR
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{doc_id}{ext}")

        # Stream the upload to disk asynchronously
        content = await file.read()
        async with aiofiles.open(save_path, "wb") as f_out:
            await f_out.write(content)

        file_size = len(content)
        file_type = ext.lstrip(".")

        logger.info("Uploaded '%s' as doc_id='%s' (%d bytes).", filename, doc_id, file_size)

        return DocumentUploadResponse(
            doc_id=doc_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            message="File uploaded successfully. Call /process-document to index it.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Upload failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc


@router.post(
    "/process-document", response_model=ProcessDocumentResponse, tags=["Documents"]
)
async def process_document(request: ProcessDocumentRequest) -> ProcessDocumentResponse:
    """Extract, chunk, embed, and index a previously uploaded document."""
    try:
        doc_id = request.document_id
        upload_dir = settings.UPLOAD_DIR

        # Find the saved file regardless of extension
        matched_path: Optional[str] = None
        matched_name: Optional[str] = None
        for fname in os.listdir(upload_dir):
            if fname.startswith(doc_id):
                matched_path = os.path.join(upload_dir, fname)
                matched_name = fname
                break

        if matched_path is None:
            raise HTTPException(
                status_code=404,
                detail=f"No file found for document_id='{doc_id}'.",
            )

        result = orchestrator.process_document(
            document_id=doc_id,
            file_path=matched_path,
            filename=matched_name or doc_id,
        )

        return ProcessDocumentResponse(
            document_id=doc_id,
            status=result["status"],
            chunk_count=result["chunk_count"],
            message=f"Document processed successfully into {result['chunk_count']} chunks.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Processing failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc


@router.get("/documents", response_model=list[DocumentInfo], tags=["Documents"])
async def list_documents() -> list[DocumentInfo]:
    """List all documents that have been uploaded."""
    try:
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            return []

        docs: list[DocumentInfo] = []
        for fname in os.listdir(upload_dir):
            fpath = os.path.join(upload_dir, fname)
            if not os.path.isfile(fpath):
                continue
            ext = os.path.splitext(fname)[1].lower().lstrip(".")
            stat = os.stat(fpath)
            doc_id = os.path.splitext(fname)[0]
            docs.append(
                DocumentInfo(
                    document_id=doc_id,
                    filename=fname,
                    file_type=ext,
                    file_size=stat.st_size,
                    uploaded_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                )
            )
        return docs
    except Exception as exc:
        logger.exception("Failed to list documents: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Question answering
# ---------------------------------------------------------------------------


@router.post("/ask-question", response_model=QuestionResponse, tags=["Q&A"])
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """Answer a research question using the RAG pipeline."""
    try:
        result = orchestrator.answer_question(
            question=request.question,
            top_k=request.top_k or 5,
        )
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            model_used=result["model_used"],
        )
    except Exception as exc:
        logger.exception("Question answering failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Summarisation
# ---------------------------------------------------------------------------


@router.post("/summarize-document", response_model=SummarizeResponse, tags=["Summaries"])
async def summarize_document(request: SummarizeRequest) -> SummarizeResponse:
    """Generate a summarization of an indexed document."""
    try:
        result = orchestrator.summarize_document(
            document_id=request.document_id,
            length=request.length,
        )
        return SummarizeResponse(
            document_id=result["document_id"],
            summary=result["summary"],
            length=result["length"],
        )
    except Exception as exc:
        logger.exception("Summarisation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Knowledge graph
# ---------------------------------------------------------------------------


@router.post(
    "/generate-knowledge-graph",
    response_model=KnowledgeGraphResponse,
    tags=["Knowledge Graph"],
)
async def generate_knowledge_graph(
    request: KnowledgeGraphRequest,
) -> KnowledgeGraphResponse:
    """Extract and return the knowledge graph for a document."""
    try:
        graph = orchestrator.generate_knowledge_graph(request.document_id)
        return KnowledgeGraphResponse(
            document_id=graph["document_id"],
            nodes=graph["nodes"],
            edges=graph["edges"],
            node_count=len(graph["nodes"]),
            edge_count=len(graph["edges"]),
        )
    except Exception as exc:
        logger.exception("Knowledge graph generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/knowledge-graph",
    response_model=KnowledgeGraphResponse,
    tags=["Knowledge Graph"],
)
async def get_knowledge_graph(
    document_id: Optional[str] = Query(default=None),
) -> KnowledgeGraphResponse:
    """Retrieve the knowledge graph, optionally filtered by document ID.

    When *document_id* is omitted all stored graph data is returned.
    """
    try:
        # Attempt Neo4j first; fall back to in-memory extraction if unavailable
        try:
            from backend.knowledge_graph.neo4j_client import Neo4jClient

            neo4j = Neo4jClient(
                uri=settings.NEO4J_URI,
                user=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
            )
            graph = neo4j.get_graph(document_id)
            neo4j.close()
        except Exception:
            # If Neo4j is unavailable, generate graph on the fly from FAISS chunks
            if document_id:
                graph = orchestrator.generate_knowledge_graph(document_id)
            else:
                graph = {"nodes": [], "edges": [], "document_id": ""}

        return KnowledgeGraphResponse(
            document_id=document_id or "",
            nodes=graph["nodes"],
            edges=graph["edges"],
            node_count=len(graph["nodes"]),
            edge_count=len(graph["edges"]),
        )
    except Exception as exc:
        logger.exception("Failed to retrieve knowledge graph: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
