import { useEffect, useState } from 'react';
import { listDocuments, summarizeDocument } from '../lib/api';

const LENGTH_OPTIONS = [
  { value: 'short', label: 'Short', desc: '2-3 sentences' },
  { value: 'medium', label: 'Medium', desc: '1 paragraph' },
  { value: 'detailed', label: 'Detailed', desc: '3 sections' },
];

export default function DocumentSummary() {
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [length, setLength] = useState('medium');
  const [summary, setSummary] = useState('');
  const [summarizing, setSummarizing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) setSelectedDocId(docs[0].document_id);
      })
      .catch(() => setError('Failed to load documents. Ensure the backend is running.'))
      .finally(() => setLoadingDocs(false));
  }, []);

  const handleSummarize = async () => {
    if (!selectedDocId) return;
    setSummarizing(true);
    setSummary('');
    setError('');
    try {
      const result = await summarizeDocument(selectedDocId, length);
      setSummary(result.summary);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Summarisation failed.');
    } finally {
      setSummarizing(false);
    }
  };

  if (loadingDocs) {
    return <p className="text-gray-500 text-sm">Loading documents…</p>;
  }

  if (documents.length === 0) {
    return (
      <div className="card max-w-lg text-center py-10">
        <p className="text-4xl mb-3">📭</p>
        <p className="text-gray-600 font-medium">No documents found.</p>
        <p className="text-sm text-gray-400 mt-1">
          Upload and process a document first, then come back here to generate summaries.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Document selector */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-gray-800">Select a Document</h2>
        <div className="space-y-2">
          {documents.map((doc) => (
            <label
              key={doc.document_id}
              className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition ${
                selectedDocId === doc.document_id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <input
                type="radio"
                name="doc"
                value={doc.document_id}
                checked={selectedDocId === doc.document_id}
                onChange={() => setSelectedDocId(doc.document_id)}
                className="accent-blue-600"
              />
              <span className="text-xl">
                {doc.file_type === 'pdf' ? '📕' : doc.file_type === 'docx' ? '📘' : '📃'}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-gray-800">{doc.filename}</p>
                <p className="text-xs text-gray-400">{doc.file_type.toUpperCase()}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Length selector */}
      <div className="card space-y-3">
        <h2 className="font-semibold text-gray-800">Summary Length</h2>
        <div className="flex gap-3">
          {LENGTH_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setLength(opt.value)}
              className={`flex-1 rounded-lg border py-2.5 text-sm font-medium transition ${
                length === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-600 hover:border-blue-300'
              }`}
            >
              <span className="block">{opt.label}</span>
              <span className="block text-xs opacity-60">{opt.desc}</span>
            </button>
          ))}
        </div>

        <button
          onClick={handleSummarize}
          disabled={!selectedDocId || summarizing}
          className="btn-primary w-full justify-center"
        >
          {summarizing ? '⏳ Generating summary…' : '✨ Generate Summary'}
        </button>
      </div>

      {/* Summary output */}
      {summary && (
        <div className="card space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">Summary</h2>
            <button
              onClick={() => navigator.clipboard?.writeText(summary)}
              className="text-xs text-gray-400 hover:text-gray-600 transition"
              title="Copy to clipboard"
            >
              📋 Copy
            </button>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{summary}</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600">
          ❌ {error}
        </div>
      )}
    </div>
  );
}
