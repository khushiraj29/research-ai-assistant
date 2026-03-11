"""Pydantic v2 request/response schemas for the Research AI Assistant API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Upload & processing
# ---------------------------------------------------------------------------


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    file_size: int
    message: str


class ProcessDocumentRequest(BaseModel):
    document_id: str


class ProcessDocumentResponse(BaseModel):
    document_id: str
    status: str
    chunk_count: int
    message: str


# ---------------------------------------------------------------------------
# Question answering
# ---------------------------------------------------------------------------


class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class SourceDict(BaseModel):
    document_id: str
    source_filename: str
    chunk_index: int
    score: float


class QuestionResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str


# ---------------------------------------------------------------------------
# Summarisation
# ---------------------------------------------------------------------------


class SummarizeRequest(BaseModel):
    document_id: str
    length: str = Field(default="medium", pattern="^(short|medium|detailed)$")


class SummarizeResponse(BaseModel):
    document_id: str
    summary: str
    length: str


# ---------------------------------------------------------------------------
# Knowledge graph
# ---------------------------------------------------------------------------


class KnowledgeGraphRequest(BaseModel):
    document_id: str


class KnowledgeGraphResponse(BaseModel):
    document_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    node_count: int
    edge_count: int


# ---------------------------------------------------------------------------
# Document listing
# ---------------------------------------------------------------------------


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
