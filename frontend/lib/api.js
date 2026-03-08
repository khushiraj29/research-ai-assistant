/**
 * Centralised API client for the Research AI Assistant frontend.
 * All requests go through this module so that the base URL is
 * configured in one place and error handling is consistent.
 */

import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

// -------------------------------------------------------------------------
// Documents
// -------------------------------------------------------------------------

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/upload-document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function processDocument(documentId) {
  const { data } = await api.post('/process-document', { document_id: documentId });
  return data;
}

export async function listDocuments() {
  const { data } = await api.get('/documents');
  return data;
}

// -------------------------------------------------------------------------
// Q&A
// -------------------------------------------------------------------------

export async function askQuestion(question, topK = 5) {
  const { data } = await api.post('/ask-question', { question, top_k: topK });
  return data;
}

// -------------------------------------------------------------------------
// Summaries
// -------------------------------------------------------------------------

export async function summarizeDocument(documentId, length = 'medium') {
  const { data } = await api.post('/summarize-document', {
    document_id: documentId,
    length,
  });
  return data;
}

// -------------------------------------------------------------------------
// Knowledge Graph
// -------------------------------------------------------------------------

export async function generateKnowledgeGraph(documentId) {
  const { data } = await api.post('/generate-knowledge-graph', {
    document_id: documentId,
  });
  return data;
}

export async function getKnowledgeGraph(documentId = null) {
  const params = documentId ? { document_id: documentId } : {};
  const { data } = await api.get('/knowledge-graph', { params });
  return data;
}

// -------------------------------------------------------------------------
// Health
// -------------------------------------------------------------------------

export async function checkHealth() {
  const { data } = await api.get('/health');
  return data;
}

export default api;
