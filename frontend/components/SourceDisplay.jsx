/**
 * SourceDisplay – renders the list of document sources returned by the
 * RAG pipeline alongside each AI answer.
 */
export default function SourceDisplay({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Sources</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {sources.map((src, idx) => (
          <div
            key={idx}
            className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600"
          >
            <div className="flex items-center gap-1 font-medium text-gray-700 truncate">
              <span>📄</span>
              <span className="truncate">{src.source_filename || 'Unknown file'}</span>
            </div>
            <div className="mt-1 flex items-center gap-3 text-gray-400">
              <span>Chunk #{src.chunk_index ?? '–'}</span>
              <span>·</span>
              <span title="L2 similarity distance (lower = more relevant)">
                Score: {typeof src.score === 'number' ? src.score.toFixed(3) : '–'}
              </span>
            </div>
            {src.document_id && (
              <div className="mt-0.5 truncate text-gray-400">
                ID: <code className="font-mono">{src.document_id.slice(0, 8)}…</code>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
