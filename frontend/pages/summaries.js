import Sidebar from '../components/Sidebar';
import DocumentSummary from '../components/DocumentSummary';

export default function SummariesPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Document Summaries</h1>
        <DocumentSummary />
      </main>
    </div>
  );
}
