import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { askQuestion } from '../lib/api';
import SourceDisplay from './SourceDisplay';

function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1 px-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-gray-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

const WELCOME = {
  id: 'welcome',
  role: 'ai',
  content:
    'Hello! I\'m your Research AI Assistant. Upload and index documents, then ask me anything about them.',
  sources: [],
};

export default function ChatInterface() {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async () => {
    const question = input.trim();
    if (!question || loading) return;

    const userMsg = { id: Date.now(), role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const data = await askQuestion(question);
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        content: data.answer,
        sources: data.sources || [],
        model: data.model_used,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-4 px-6 py-6">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              {msg.role === 'ai' && (
                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                  <span>🤖</span>
                  <span>AI Assistant</span>
                  {msg.model && <span className="text-gray-300">· {msg.model}</span>}
                </div>
              )}
              <div className={msg.role === 'user' ? 'bubble-user' : 'bubble-ai'}>
                {msg.role === 'ai' ? (
                  <ReactMarkdown className="prose prose-sm max-w-none prose-p:my-1 prose-headings:my-2">
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
              {msg.role === 'ai' && msg.sources?.length > 0 && (
                <SourceDisplay sources={msg.sources} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bubble-ai">
              <TypingDots />
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-2 text-sm text-red-600">
            ❌ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <div className="flex items-end gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents… (Enter to send)"
            rows={2}
            className="input-field resize-none flex-1"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="btn-primary px-5 py-3 h-full self-stretch"
          >
            {loading ? '⏳' : '➤'}
          </button>
        </div>
        <p className="mt-1.5 text-xs text-gray-400">
          Shift+Enter for new line · Enter to send
        </p>
      </div>
    </div>
  );
}
