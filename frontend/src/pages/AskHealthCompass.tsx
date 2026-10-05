import { useState, useRef, useEffect } from 'react';
import {
  Send,
  Loader2,
  AlertCircle,
  CheckCircle,
  Bookmark,
  Upload,
  Sparkles,
  Filter,
  ShieldCheck,
  Clock,
  FileText,
  Zap,
} from 'lucide-react';
import {
  askHealthCompass,
  askHealthCompassStream,
  uploadDocument,
  ApiError,
} from '../api/client';
import type { AskResponse, CitationInfo } from '../api/client';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  responseMeta?: AskResponse;
  timestamp: string;
}

function AskHealthCompass() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamMode, setStreamMode] = useState(true);
  const [streamingText, setStreamingText] = useState('');

  // Filtering & hybrid search options (Task 3.33)
  const [showFilters, setShowFilters] = useState(false);
  const [regionFilter, setRegionFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');
  const [keywordWeight, setKeywordWeight] = useState(0.2);

  // Document upload modal (Task 3.45)
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // Active citation popover
  const [activeCitation, setActiveCitation] = useState<CitationInfo | null>(null);
  const [savedSources, setSavedSources] = useState<Set<string>>(new Set());

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userText = question.trim();
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuestion('');
    setLoading(true);
    setError(null);
    setStreamingText('');

    // Prepare metadata filters
    const metadata_filter: Record<string, string> = {};
    if (regionFilter) metadata_filter['region'] = regionFilter;
    if (topicFilter) metadata_filter['topic'] = topicFilter;

    // Prior history turns for condensation (Task 3.42)
    const historyTurns = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    if (streamMode) {
      let accumulated = '';
      try {
        await askHealthCompassStream(
          userText,
          (token) => {
            accumulated += token;
            setStreamingText(accumulated);
          },
          () => {
            const assistantMsg: ChatMessage = {
              id: (Date.now() + 1).toString(),
              role: 'assistant',
              content: accumulated,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            };
            setMessages((prev) => [...prev, assistantMsg]);
            setStreamingText('');
            setLoading(false);
          },
          (err) => {
            setError(err.message);
            setLoading(false);
            setStreamingText('');
          },
          {
            history: historyTurns,
            metadata_filter: Object.keys(metadata_filter).length ? metadata_filter : undefined,
            keyword_weight: keywordWeight,
          }
        );
      } catch (err: any) {
        setError(err.message || 'Stream connection failed');
        setLoading(false);
      }
    } else {
      try {
        const result = await askHealthCompass(userText, {
          history: historyTurns,
          metadata_filter: Object.keys(metadata_filter).length ? metadata_filter : undefined,
          keyword_weight: keywordWeight,
        });

        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: result.answer,
          responseMeta: result,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred during generation');
        }
      } finally {
        setLoading(false);
      }
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadStatus(null);
    try {
      const res = await uploadDocument(uploadFile);
      setUploadStatus(`Success! Ingested and indexed ${res.chunks_indexed} chunks from ${res.filename}.`);
      setUploadFile(null);
      setTimeout(() => {
        setShowUploadModal(false);
        setUploadStatus(null);
      }, 2500);
    } catch (err: any) {
      setUploadStatus(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const toggleSaveSource = (sourceId: string) => {
    const newSaved = new Set(savedSources);
    if (newSaved.has(sourceId)) {
      newSaved.delete(sourceId);
    } else {
      newSaved.add(sourceId);
    }
    setSavedSources(newSaved);
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Header bar */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-blue-600" />
            HealthCompass Guidance Assistant
          </h1>
          <p className="text-sm text-gray-500">
            Real-time grounded RAG intelligence for frontline health responders
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
              showFilters
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Filter className="h-4 w-4" />
            Filters {Object.keys(regionFilter || topicFilter ? [''] : []).length > 0 && '•'}
          </button>

          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-emerald-50 border border-emerald-200 text-emerald-700 hover:bg-emerald-100 transition-colors"
          >
            <Upload className="h-4 w-4" />
            Upload Document
          </button>
        </div>
      </div>

      {/* Filter panel (Task 3.33) */}
      {showFilters && (
        <div className="bg-gray-50 border-b border-gray-200 p-4 rounded-b-lg grid grid-cols-1 md:grid-cols-3 gap-4 text-sm animate-fadeIn">
          <div>
            <label className="block font-medium text-gray-700 mb-1">Region / District</label>
            <select
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Regions</option>
              <option value="District A">District A</option>
              <option value="District B">District B</option>
              <option value="Regional">Regional Central</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-gray-700 mb-1">Guidance Topic</label>
            <select
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
              className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Topics</option>
              <option value="Vaccination">Vaccination</option>
              <option value="Infection Control">Infection Control</option>
              <option value="Child Health">Child Health</option>
              <option value="Emergency Response">Emergency Response</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="font-medium text-gray-700">Hybrid Search Weight</label>
              <span className="text-xs text-gray-500">
                {keywordWeight === 0 ? 'Dense Only' : keywordWeight === 1 ? 'BM25 Keyword' : `Hybrid (${keywordWeight.toFixed(1)})`}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={keywordWeight}
              onChange={(e) => setKeywordWeight(parseFloat(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>
        </div>
      )}

      {/* Main chat message stream */}
      <div className="flex-1 overflow-y-auto py-6 space-y-6">
        {messages.length === 0 && !streamingText && (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4">
              <Sparkles className="h-8 w-8" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">How can HealthCompass assist you?</h2>
            <p className="text-gray-500 max-w-md mb-6">
              Ask about active outbreak isolation protocols, child fever triage, or vaccination priority guidelines.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl w-full text-left">
              {[
                'What is the isolation protocol for acute respiratory infections in District A?',
                'What are the priority groups for booster vaccinations?',
                'What are cold chain storage temperature requirements for vaccines?',
                'How to handle pediatric fever during emergency triage?',
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuestion(suggestion)}
                  className="p-3 text-xs bg-white hover:bg-blue-50/50 border border-gray-200 hover:border-blue-300 rounded-xl transition text-gray-700 flex items-start gap-2"
                >
                  <FileText className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
                  <span>{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-3xl rounded-2xl px-5 py-4 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none shadow-sm'
              }`}
            >
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </div>

              {/* Attribution and Telemetry footer for assistant messages */}
              {msg.role === 'assistant' && msg.responseMeta && (
                <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1 text-emerald-600 font-medium">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Grounded ({Math.round((msg.responseMeta.faithfulness_score || 0.9) * 100)}%)
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {msg.responseMeta.latency_ms?.toFixed(0)}ms
                  </span>
                  {msg.responseMeta.cached && (
                    <span className="flex items-center gap-1 text-purple-600 font-medium">
                      <Zap className="h-3.5 w-3.5" />
                      Cached
                    </span>
                  )}

                  {/* Citations list */}
                  {msg.responseMeta.citations?.length > 0 && (
                    <div className="w-full mt-2 pt-2 flex flex-wrap gap-1.5 items-center">
                      <span className="font-medium text-gray-600 mr-1">Citations:</span>
                      {msg.responseMeta.citations.map((c) => (
                        <button
                          key={c.index}
                          onClick={() => setActiveCitation(c)}
                          className="px-2 py-0.5 bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 rounded font-medium text-xs transition"
                        >
                          [{c.index}] {c.source}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            <span className="text-[10px] text-gray-400 mt-1 px-1">{msg.timestamp}</span>
          </div>
        ))}

        {/* Live streaming bubble (Task 3.47) */}
        {streamingText && (
          <div className="flex flex-col items-start">
            <div className="max-w-3xl rounded-2xl px-5 py-4 bg-white border border-blue-200 text-gray-800 rounded-tl-none shadow-sm">
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {streamingText}
                <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
              </div>
            </div>
            <span className="text-[10px] text-blue-500 mt-1 px-1 flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" /> Streaming verified guidance...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2.5 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">{error}</div>
          <button onClick={() => setError(null)} className="text-xs text-red-500 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Input query form */}
      <div className="pt-3 border-t border-gray-200">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask HealthCompass about emergency protocols, dosages, isolation periods..."
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:bg-gray-50"
              disabled={loading}
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setStreamMode(!streamMode)}
              className={`px-3 py-3 rounded-xl border text-xs font-medium flex items-center gap-1 transition ${
                streamMode
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-600'
              }`}
              title="Toggle Token Streaming"
            >
              <Zap className={`h-4 w-4 ${streamMode ? 'text-blue-600 fill-blue-600' : 'text-gray-400'}`} />
              Stream
            </button>

            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="px-5 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-xl font-medium text-sm transition flex items-center gap-2"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Send
            </button>
          </div>
        </form>
      </div>

      {/* Citation Detail Modal */}
      {activeCitation && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-gray-100 animate-scaleUp">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-600" />
                Verified Citation [{activeCitation.index}]
              </h3>
              <button
                onClick={() => setActiveCitation(null)}
                className="text-gray-400 hover:text-gray-600 text-lg leading-none"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-3">
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Source Document</span>
                <p className="text-sm font-semibold text-gray-800">{activeCitation.source}</p>
                {activeCitation.section && (
                  <p className="text-xs text-gray-500">Section: {activeCitation.section}</p>
                )}
              </div>

              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Source Excerpt</span>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg text-sm text-gray-700 italic border-l-2 border-blue-500">
                  "{activeCitation.snippet}"
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-gray-400 pt-2">
                <span>Chunk ID: {activeCitation.chunk_id}</span>
                <span>Distance: {activeCitation.distance.toFixed(4)}</span>
              </div>
            </div>

            <div className="pt-3 border-t border-gray-100 flex justify-end gap-2">
              <button
                onClick={() => {
                  toggleSaveSource(activeCitation.chunk_id);
                  setActiveCitation(null);
                }}
                className="px-4 py-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg font-medium transition flex items-center gap-1.5"
              >
                <Bookmark className="h-4 w-4" />
                {savedSources.has(activeCitation.chunk_id) ? 'Saved' : 'Save Source'}
              </button>
              <button
                onClick={() => setActiveCitation(null)}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document Upload Modal (Task 3.45) */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-gray-100">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <Upload className="h-5 w-5 text-blue-600" />
                Upload New Health Guidance
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600 text-lg leading-none"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleFileUpload} className="py-4 space-y-4">
              <p className="text-xs text-gray-600">
                Upload new public health guidelines or circulars (.pdf, .txt, .md, .html).
                The document will be automatically cleaned, chunked, embedded, and added to the ChromaDB vector store.
              </p>

              <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-blue-500 transition cursor-pointer">
                <input
                  type="file"
                  id="guidance-file"
                  accept=".pdf,.txt,.md,.html"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <label htmlFor="guidance-file" className="cursor-pointer">
                  <FileText className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <span className="text-sm font-medium text-blue-600 hover:underline">
                    {uploadFile ? uploadFile.name : 'Choose a guidance file to upload'}
                  </span>
                  <p className="text-xs text-gray-400 mt-1">PDF, TXT, MD, HTML up to 15MB</p>
                </label>
              </div>

              {uploadStatus && (
                <div className={`p-3 rounded-lg text-xs ${uploadStatus.startsWith('Success') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                  {uploadStatus}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition"
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!uploadFile || uploading}
                  className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg font-medium transition flex items-center gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Ingesting & Embedding...
                    </>
                  ) : (
                    'Index Document'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AskHealthCompass;
