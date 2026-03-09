/**
 * Tests for frontend/lib/api.js – the centralised Axios API client.
 *
 * All HTTP requests are intercepted by axios-mock-adapter so no real server
 * is needed.  Run with: npm test  (from the frontend/ directory)
 */

import MockAdapter from 'axios-mock-adapter';
import api, {
  askQuestion,
  checkHealth,
  generateKnowledgeGraph,
  getKnowledgeGraph,
  listDocuments,
  processDocument,
  summarizeDocument,
  uploadDocument,
} from '../lib/api';

// Create a mock adapter that intercepts requests on the shared axios instance.
const mock = new MockAdapter(api);

afterEach(() => {
  mock.reset();
});

// ---------------------------------------------------------------------------
// checkHealth
// ---------------------------------------------------------------------------

describe('checkHealth', () => {
  it('calls GET /health and returns data', async () => {
    const payload = { status: 'healthy', message: 'OK', version: '0.1.0' };
    mock.onGet('/health').reply(200, payload);

    const result = await checkHealth();
    expect(result).toEqual(payload);
  });
});

// ---------------------------------------------------------------------------
// listDocuments
// ---------------------------------------------------------------------------

describe('listDocuments', () => {
  it('calls GET /documents and returns an array', async () => {
    const docs = [
      { document_id: 'doc-1', filename: 'paper.txt', file_type: 'txt', file_size: 512, uploaded_at: '2024-01-01T00:00:00' },
    ];
    mock.onGet('/documents').reply(200, docs);

    const result = await listDocuments();
    expect(result).toHaveLength(1);
    expect(result[0].document_id).toBe('doc-1');
  });

  it('returns empty array when no documents exist', async () => {
    mock.onGet('/documents').reply(200, []);
    const result = await listDocuments();
    expect(result).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// uploadDocument
// ---------------------------------------------------------------------------

describe('uploadDocument', () => {
  it('calls POST /upload-document with FormData and returns doc_id', async () => {
    const payload = {
      doc_id: 'abc-123',
      filename: 'paper.txt',
      file_type: 'txt',
      file_size: 256,
      message: 'Uploaded successfully.',
    };
    mock.onPost('/upload-document').reply(200, payload);

    const file = new File(['hello world'], 'paper.txt', { type: 'text/plain' });
    const result = await uploadDocument(file);
    expect(result.doc_id).toBe('abc-123');
    expect(result.filename).toBe('paper.txt');
  });
});

// ---------------------------------------------------------------------------
// processDocument
// ---------------------------------------------------------------------------

describe('processDocument', () => {
  it('calls POST /process-document with document_id', async () => {
    const payload = {
      document_id: 'abc-123',
      status: 'success',
      chunk_count: 8,
      message: 'Processed.',
    };
    mock.onPost('/process-document').reply(200, payload);

    const result = await processDocument('abc-123');
    expect(result.chunk_count).toBe(8);
    expect(result.status).toBe('success');
  });
});

// ---------------------------------------------------------------------------
// askQuestion
// ---------------------------------------------------------------------------

describe('askQuestion', () => {
  it('calls POST /ask-question and returns answer + sources', async () => {
    const payload = {
      answer: 'AI stands for Artificial Intelligence.',
      sources: [{ document_id: 'doc-1', source_filename: 'paper.txt', chunk_index: 0, score: 0.3 }],
      model_used: 'gpt-3.5-turbo',
    };
    mock.onPost('/ask-question').reply(200, payload);

    const result = await askQuestion('What is AI?');
    expect(result.answer).toBe('AI stands for Artificial Intelligence.');
    expect(result.sources).toHaveLength(1);
    expect(result.model_used).toBe('gpt-3.5-turbo');
  });

  it('sends default top_k of 5', async () => {
    mock.onPost('/ask-question').reply((config) => {
      const body = JSON.parse(config.data);
      expect(body.top_k).toBe(5);
      return [200, { answer: '', sources: [], model_used: 'gpt-3.5-turbo' }];
    });
    await askQuestion('test question');
  });

  it('sends custom top_k when provided', async () => {
    mock.onPost('/ask-question').reply((config) => {
      const body = JSON.parse(config.data);
      expect(body.top_k).toBe(3);
      return [200, { answer: '', sources: [], model_used: 'gpt-3.5-turbo' }];
    });
    await askQuestion('test', 3);
  });
});

// ---------------------------------------------------------------------------
// summarizeDocument
// ---------------------------------------------------------------------------

describe('summarizeDocument', () => {
  it('calls POST /summarize-document with document_id and length', async () => {
    const payload = {
      document_id: 'doc-1',
      summary: 'This paper discusses AI.',
      length: 'short',
    };
    mock.onPost('/summarize-document').reply(200, payload);

    const result = await summarizeDocument('doc-1', 'short');
    expect(result.summary).toBe('This paper discusses AI.');
  });

  it('uses medium as the default length', async () => {
    mock.onPost('/summarize-document').reply((config) => {
      const body = JSON.parse(config.data);
      expect(body.length).toBe('medium');
      return [200, { document_id: 'doc-1', summary: '', length: 'medium' }];
    });
    await summarizeDocument('doc-1');
  });
});

// ---------------------------------------------------------------------------
// generateKnowledgeGraph
// ---------------------------------------------------------------------------

describe('generateKnowledgeGraph', () => {
  it('calls POST /generate-knowledge-graph with document_id', async () => {
    const payload = {
      document_id: 'doc-1',
      nodes: [{ id: 'AI', label: 'AI', entity_type: 'ORG' }],
      edges: [],
      node_count: 1,
      edge_count: 0,
    };
    mock.onPost('/generate-knowledge-graph').reply(200, payload);

    const result = await generateKnowledgeGraph('doc-1');
    expect(result.node_count).toBe(1);
    expect(result.nodes[0].id).toBe('AI');
  });
});

// ---------------------------------------------------------------------------
// getKnowledgeGraph
// ---------------------------------------------------------------------------

describe('getKnowledgeGraph', () => {
  it('calls GET /knowledge-graph without params when no document_id', async () => {
    const payload = { document_id: '', nodes: [], edges: [], node_count: 0, edge_count: 0 };
    mock.onGet('/knowledge-graph').reply(200, payload);

    const result = await getKnowledgeGraph();
    expect(result.nodes).toEqual([]);
  });

  it('passes document_id as query param when provided', async () => {
    const payload = {
      document_id: 'doc-1',
      nodes: [{ id: 'Solar Energy', label: 'Solar Energy', entity_type: 'ORG' }],
      edges: [],
      node_count: 1,
      edge_count: 0,
    };
    mock.onGet('/knowledge-graph', { params: { document_id: 'doc-1' } }).reply(200, payload);

    const result = await getKnowledgeGraph('doc-1');
    expect(result.document_id).toBe('doc-1');
  });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

describe('error propagation', () => {
  it('rejects with error on server 500', async () => {
    mock.onGet('/health').reply(500, { detail: 'Internal server error' });
    await expect(checkHealth()).rejects.toThrow();
  });

  it('rejects with error on network failure', async () => {
    mock.onGet('/health').networkError();
    await expect(checkHealth()).rejects.toThrow();
  });
});
