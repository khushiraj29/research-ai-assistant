import { useEffect, useState } from 'react';
import Link from 'next/link';
import { checkHealth, listDocuments } from '../lib/api';

const NAV_CARDS = [
  {
    href: '/upload',
    title: 'Upload Documents',
    description: 'Upload PDF, DOCX, or TXT research documents and index them for AI search.',
    icon: '📄',
    color: 'from-blue-500 to-blue-600',
  },
  {
    href: '/chat',
    title: 'Chat with AI',
    description: 'Ask natural-language questions and get answers grounded in your documents.',
    icon: '💬',
    color: 'from-purple-500 to-purple-600',
  },
  {
    href: '/summaries',
    title: 'Summaries',
    description: 'Generate short, medium, or detailed summaries of any uploaded document.',
    icon: '📝',
    color: 'from-emerald-500 to-emerald-600',
  },
  {
    href: '/knowledge-graph',
    title: 'Knowledge Graph',
    description: 'Explore entity relationships extracted from your documents visually.',
    icon: '🕸️',
    color: 'from-orange-500 to-orange-600',
  },
];

export default function Home() {
  const [health, setHealth] = useState(null);
  const [docCount, setDocCount] = useState(0);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'unreachable' }));

    listDocuments()
      .then((docs) => setDocCount(docs.length))
      .catch(() => setDocCount(0));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 bg-white/5 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🔬</span>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Research AI Assistant</h1>
              <p className="text-xs text-blue-300">Powered by RAG + LangChain + GPT</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
              }`}
            />
            <span className="text-xs text-gray-300">
              {health?.status === 'healthy' ? 'API Online' : 'API Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="mx-auto max-w-6xl px-6 py-12">
        <div className="mb-10 text-center">
          <h2 className="mb-3 text-4xl font-extrabold tracking-tight">
            Your Intelligent Research Companion
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-blue-200">
            Upload research papers, ask questions, generate summaries, and explore knowledge
            graphs — all powered by state-of-the-art AI.
          </p>
        </div>

        {/* Stats */}
        <div className="mb-10 flex justify-center gap-8">
          <div className="rounded-2xl bg-white/10 px-8 py-5 text-center backdrop-blur-sm">
            <p className="text-4xl font-bold text-blue-300">{docCount}</p>
            <p className="mt-1 text-sm text-gray-300">Documents Uploaded</p>
          </div>
          <div className="rounded-2xl bg-white/10 px-8 py-5 text-center backdrop-blur-sm">
            <p className="text-4xl font-bold text-purple-300">RAG</p>
            <p className="mt-1 text-sm text-gray-300">Pipeline Active</p>
          </div>
          <div className="rounded-2xl bg-white/10 px-8 py-5 text-center backdrop-blur-sm">
            <p className="text-4xl font-bold text-emerald-300">v0.1</p>
            <p className="mt-1 text-sm text-gray-300">Current Version</p>
          </div>
        </div>

        {/* Navigation cards */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {NAV_CARDS.map((card) => (
            <Link key={card.href} href={card.href} className="group block">
              <div className="h-full rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm transition duration-200 hover:border-white/30 hover:bg-white/10">
                <div
                  className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${card.color} text-2xl shadow-lg`}
                >
                  {card.icon}
                </div>
                <h3 className="mb-2 font-semibold text-white group-hover:text-blue-300 transition">
                  {card.title}
                </h3>
                <p className="text-sm text-gray-400">{card.description}</p>
              </div>
            </Link>
          ))}
        </div>

        {/* Quick-start tip */}
        <div className="mt-10 rounded-2xl border border-blue-500/30 bg-blue-500/10 px-6 py-4 text-sm text-blue-200">
          <strong>Quick start:</strong> Upload a document → Process it → Ask a question or
          generate a knowledge graph. Check the{' '}
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="underline hover:text-white"
          >
            API docs
          </a>{' '}
          at <code>localhost:8000/docs</code>.
        </div>
      </main>
    </div>
  );
}
