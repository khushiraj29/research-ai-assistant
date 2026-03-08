import Sidebar from '../components/Sidebar';
import KnowledgeGraph from '../components/KnowledgeGraph';

export default function KnowledgeGraphPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex flex-1 flex-col">
        <div className="border-b border-gray-200 bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Graph</h1>
          <p className="text-sm text-gray-500">
            Visualise entity relationships extracted from your documents.
          </p>
        </div>
        <div className="flex-1 p-8">
          <KnowledgeGraph />
        </div>
      </main>
    </div>
  );
}
