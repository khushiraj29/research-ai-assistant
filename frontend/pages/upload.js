import Sidebar from '../components/Sidebar';
import DocumentUpload from '../components/DocumentUpload';

export default function UploadPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Upload Documents</h1>
        <DocumentUpload />
      </main>
    </div>
  );
}
