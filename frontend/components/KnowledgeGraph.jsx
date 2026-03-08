/**
 * KnowledgeGraph – interactive force-directed graph visualisation.
 *
 * react-force-graph-2d relies on browser APIs (canvas, ResizeObserver) that
 * are not available during Next.js server-side rendering, so the component is
 * loaded with a dynamic import and ssr: false (see pages/knowledge-graph.js).
 * The dynamic import wrapper is handled here to keep page files clean.
 */
import dynamic from 'next/dynamic';
import { useEffect, useRef, useState } from 'react';
import { getKnowledgeGraph, listDocuments } from '../lib/api';

// Dynamic import to disable SSR for the canvas-based graph renderer
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

const NODE_COLORS = {
  ORG: '#3b82f6',
  PERSON: '#10b981',
  GPE: '#f59e0b',
  LOC: '#8b5cf6',
  PRODUCT: '#ef4444',
  EVENT: '#ec4899',
  WORK_OF_ART: '#06b6d4',
  DATE: '#6b7280',
  DEFAULT: '#94a3b8',
};

function getNodeColor(node) {
  return NODE_COLORS[node.entity_type] || NODE_COLORS.DEFAULT;
}

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const fgRef = useRef();

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch(() => {});
  }, []);

  const loadGraph = async (docId) => {
    setLoading(true);
    setError('');
    setSelectedNode(null);
    try {
      const data = await getKnowledgeGraph(docId || null);
      // react-force-graph-2d expects "links" not "edges"
      setGraphData({
        nodes: data.nodes.map((n) => ({ ...n, id: n.id ?? n.label })),
        links: (data.edges || []).map((e) => ({
          source: e.source,
          target: e.target,
          label: e.relationship,
        })),
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load graph.');
    } finally {
      setLoading(false);
    }
  };

  const isEmpty = graphData.nodes.length === 0;

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={selectedDocId}
          onChange={(e) => setSelectedDocId(e.target.value)}
          className="input-field w-64"
        >
          <option value="">All documents</option>
          {documents.map((doc) => (
            <option key={doc.document_id} value={doc.document_id}>
              {doc.filename}
            </option>
          ))}
        </select>

        <button
          onClick={() => loadGraph(selectedDocId)}
          disabled={loading}
          className="btn-primary"
        >
          {loading ? '⏳ Loading…' : '🔄 Load Graph'}
        </button>

        {!isEmpty && (
          <span className="text-sm text-gray-500">
            {graphData.nodes.length} nodes · {graphData.links.length} edges
          </span>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-2 text-sm text-red-600">
          ❌ {error}
        </div>
      )}

      {/* Legend */}
      {!isEmpty && (
        <div className="flex flex-wrap gap-2 text-xs">
          {Object.entries(NODE_COLORS)
            .filter(([k]) => k !== 'DEFAULT')
            .map(([type, color]) => (
              <span key={type} className="flex items-center gap-1">
                <span className="h-3 w-3 rounded-full inline-block" style={{ background: color }} />
                {type}
              </span>
            ))}
        </div>
      )}

      {/* Graph canvas */}
      <div className="relative flex-1 min-h-[500px] rounded-2xl border border-gray-200 bg-gray-900 overflow-hidden">
        {isEmpty && !loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
            <span className="text-5xl mb-3">🕸️</span>
            <p className="font-medium">No graph data</p>
            <p className="text-sm mt-1">Select a document and click Load Graph</p>
          </div>
        )}

        {!isEmpty && (
          <ForceGraph2D
            ref={fgRef}
            graphData={graphData}
            nodeLabel={(node) => `${node.label} (${node.entity_type || 'ENTITY'})`}
            nodeColor={getNodeColor}
            nodeRelSize={6}
            linkLabel={(link) => link.label}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkColor={() => 'rgba(148,163,184,0.5)'}
            backgroundColor="#111827"
            onNodeClick={(node) => setSelectedNode(node)}
            nodeCanvasObjectMode={() => 'after'}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.label || node.id;
              const fontSize = Math.max(10 / globalScale, 3);
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = 'rgba(255,255,255,0.85)';
              ctx.fillText(label, node.x, node.y + 10 / globalScale);
            }}
          />
        )}
      </div>

      {/* Node detail panel */}
      {selectedNode && (
        <div className="card flex items-start justify-between">
          <div>
            <p className="font-semibold text-gray-800">{selectedNode.label || selectedNode.id}</p>
            <p className="text-sm text-gray-500 mt-1">
              Type: <span className="font-medium">{selectedNode.entity_type || 'ENTITY'}</span>
            </p>
            {selectedNode.document_id && (
              <p className="text-xs text-gray-400 mt-0.5">
                Document: <code className="font-mono">{selectedNode.document_id.slice(0, 12)}…</code>
              </p>
            )}
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="text-gray-400 hover:text-gray-600 transition text-lg"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
