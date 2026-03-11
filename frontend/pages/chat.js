import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';

export default function ChatPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex flex-1 flex-col">
        <div className="border-b border-gray-200 bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Chat with AI</h1>
          <p className="text-sm text-gray-500">Ask questions about your uploaded documents.</p>
        </div>
        <ChatInterface />
      </main>
    </div>
  );
}
