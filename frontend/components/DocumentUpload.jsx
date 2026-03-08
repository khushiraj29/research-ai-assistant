import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument, processDocument } from '../lib/api';

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
};

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [processResult, setProcessResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) {
      setFile(accepted[0]);
      setUploadResult(null);
      setProcessResult(null);
      setError('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const result = await uploadDocument(file);
      setUploadResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async () => {
    if (!uploadResult?.doc_id) return;
    setProcessing(true);
    setError('');
    try {
      const result = await processDocument(uploadResult.doc_id);
      setProcessResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Processing failed.');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="max-w-xl space-y-6">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50/40'
        }`}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-3">📂</div>
        {isDragActive ? (
          <p className="text-blue-600 font-medium">Drop the file here…</p>
        ) : (
          <>
            <p className="font-medium text-gray-700">
              Drag & drop a file, or <span className="text-blue-600 underline">browse</span>
            </p>
            <p className="mt-1 text-sm text-gray-400">Supported: PDF, DOCX, TXT</p>
          </>
        )}
      </div>

      {/* Selected file info */}
      {file && (
        <div className="card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {file.name.endsWith('.pdf') ? '📕' : file.name.endsWith('.docx') ? '📘' : '📃'}
            </span>
            <div>
              <p className="text-sm font-medium text-gray-800 truncate max-w-xs">{file.name}</p>
              <p className="text-xs text-gray-400">{formatBytes(file.size)}</p>
            </div>
          </div>
          <button
            onClick={() => {
              setFile(null);
              setUploadResult(null);
              setProcessResult(null);
            }}
            className="text-gray-400 hover:text-red-500 transition text-lg"
          >
            ✕
          </button>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleUpload}
          disabled={!file || uploading || !!uploadResult}
          className="btn-primary"
        >
          {uploading ? '⏳ Uploading…' : uploadResult ? '✓ Uploaded' : '⬆ Upload'}
        </button>

        <button
          onClick={handleProcess}
          disabled={!uploadResult || processing || !!processResult}
          className="btn-primary"
          style={{ background: processResult ? '#10b981' : undefined }}
        >
          {processing ? '⏳ Indexing…' : processResult ? '✓ Indexed' : '⚙ Process & Index'}
        </button>
      </div>

      {/* Status messages */}
      {uploadResult && !processResult && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-700">
          ✅ Uploaded as <code className="font-mono text-xs">{uploadResult.doc_id}</code>. Now click{' '}
          <strong>Process & Index</strong> to make it searchable.
        </div>
      )}

      {processResult && (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700">
          🎉 Document indexed into{' '}
          <strong>{processResult.chunk_count} chunks</strong>. You can now ask questions or
          generate a summary!
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
