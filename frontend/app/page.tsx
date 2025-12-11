'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; content: string; sources?: any[] }[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [userRole, setUserRole] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Decode JWT to get user role
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUserRole(payload.role || 'paralegal');
    } catch (error) {
      console.error('Failed to decode token:', error);
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    setUploading(true);
    setUploadStatus('Uploading...');

    const formData = new FormData();
    formData.append('file', e.target.files[0]);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Upload failed');
      }

      const data = await res.json();
      setUploadStatus(`Uploaded: ${data.filename} (${data.chunks} chunks)`);
    } catch (error: any) {
      console.error(error);
      setUploadStatus(`Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    const newMessages = [...messages, { role: 'user' as const, content: query }];
    setMessages(newMessages);
    setQuery('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        if (res.status === 401) {
          router.push('/login');
          return;
        }
        throw new Error('Failed to fetch');
      }

      const data = await res.json();
      setMessages([...newMessages, { role: 'ai', content: data.response, sources: data.sources }]);
    } catch (error) {
      console.error(error);
      setMessages([...newMessages, { role: 'ai', content: 'Sorry, something went wrong.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (messageIndex: number, rating: string) => {
    const msg = messages[messageIndex];
    if (msg.role !== 'ai') return;

    // Find the user's query (previous message)
    const userQuery = messageIndex > 0 ? messages[messageIndex - 1].content : '';

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: userQuery,
          response: msg.content,
          rating: rating,
          categories: [],
          comment: ''
        }),
      });

      if (res.ok) {
        alert(rating === 'thumbs_up' ? 'Thanks for your feedback!' : 'Thanks! We\'ll work on improving.');
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
      alert('Failed to copy');
    }
  };

  const handleShare = async (text: string) => {
    try {
      await navigator.clipboard.writeText(window.location.href + '\n\n' + text);
      alert('Link and response copied to clipboard!');
    } catch (error) {
      console.error('Failed to share:', error);
    }
  };

  const handleReadAloud = (text: string) => {
    if ('speechSynthesis' in window) {
      // Stop any ongoing speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      window.speechSynthesis.speak(utterance);
    } else {
      alert('Text-to-speech is not supported in your browser');
    }
  };

  const [listening, setListening] = useState(false);

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert("Browser doesn't support speech recognition. Try Chrome.");
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuery((prev) => prev ? prev + ' ' + transcript : transcript);
      setListening(false);
    };

    recognition.onerror = (event: any) => {
      if (event.error === 'no-speech') {
        // Just stop listening, no need to alert
        return;
      }
      console.error("Speech recognition error", event.error);
      alert("Error occurred in recognition: " + event.error);
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.start();
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-50">
      <div className="w-full max-w-4xl flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Legal AI Assistant</h1>
        <div className="flex items-center gap-4">
          {userRole && (
            <span className="text-sm text-gray-600 capitalize">
              Role: <span className="font-semibold">{userRole}</span>
            </span>
          )}
          <a
            href="/settings"
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-600 rounded hover:bg-gray-50"
          >
            Settings
          </a>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm text-red-600 hover:text-red-800"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Upload Section - Only for Admin and Lawyer */}
      {userRole && (userRole === 'admin' || userRole === 'lawyer') && (
        <div className="w-full max-w-4xl mb-8 p-6 bg-white rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">1. Upload Documents</h2>
          <input
            type="file"
            onChange={handleUpload}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          {uploading && <p className="mt-2 text-blue-600">Processing file...</p>}
          {uploadStatus && <p className="mt-2 text-sm text-gray-600">{uploadStatus}</p>}
        </div>
      )}

      {/* Chat Section */}
      <div className="w-full max-w-4xl flex-grow flex flex-col bg-white rounded-lg shadow-md overflow-hidden h-[600px]">
        <div className="flex-grow overflow-y-auto p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-4 rounded-lg ${msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                <p>{msg.content}</p>
                {msg.sources && (
                  <div className="mt-2 pt-2 border-t border-gray-200 text-xs">
                    <p className="font-semibold">Sources:</p>
                    {msg.sources.map((src: any, i: number) => (
                      <div key={i} className="mt-1">
                        <span className="font-medium">{src.file}</span> (Page {src.page})
                        {src.text && <div className="mt-1 p-1 bg-gray-200 rounded italic truncate">{src.text}</div>}
                      </div>
                    ))}
                  </div>
                )}
                {/* Feedback and Interaction Buttons - Only for AI responses */}
                {msg.role === 'ai' && (
                  <div className="mt-3 pt-3 border-t border-gray-300 flex flex-wrap gap-2">
                    <button
                      onClick={() => handleFeedback(idx, 'thumbs_up')}
                      className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                      title="Helpful"
                    >
                      👍 Helpful
                    </button>
                    <button
                      onClick={() => handleFeedback(idx, 'thumbs_down')}
                      className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                      title="Not Helpful"
                    >
                      👎 Not Helpful
                    </button>
                    <button
                      onClick={() => handleCopy(msg.content)}
                      className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                      title="Copy"
                    >
                      📋 Copy
                    </button>
                    <button
                      onClick={() => handleShare(msg.content)}
                      className="px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
                      title="Share"
                    >
                      🔗 Share
                    </button>
                    <button
                      onClick={() => handleReadAloud(msg.content)}
                      className="px-3 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
                      title="Read Aloud"
                    >
                      🔊 Read Aloud
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && <div className="text-center text-gray-500">Thinking...</div>}
        </div>

        <div className="p-4 border-t bg-gray-50">
          <div className="flex gap-4">
            <button
              onClick={startListening}
              className={`p-3 rounded-lg border ${listening ? 'bg-red-100 text-red-600 border-red-300 animate-pulse' : 'bg-white text-gray-500 border-gray-300 hover:bg-gray-100'}`}
              title="Dictate Query"
            >
              🎤
            </button>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
              placeholder={listening ? "Listening..." : "Ask a legal question..."}
              className="flex-grow p-3 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={handleQuery}
              disabled={loading}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
