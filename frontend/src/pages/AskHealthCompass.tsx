import { useState } from 'react';
import { Send, Loader2, AlertCircle, CheckCircle, Bookmark } from 'lucide-react';
import { askHealthCompass, ApiError } from '../api/client';
import type { AskResponse } from '../api/client';

function AskHealthCompass() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [savedSources, setSavedSources] = useState<Set<string>>(new Set());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await askHealthCompass(question);
      setResponse(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
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
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Ask HealthCompass</h1>
        <p className="text-gray-600">
          Get evidence-based guidance from the HealthCompass knowledge base
        </p>
      </div>

      {/* Ask form */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about symptoms, protocols, prevention, or field guidance..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Send className="h-5 w-5" />
                Ask HealthCompass
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-orange-900 mb-1">Service Currently Unavailable</h3>
            <p className="text-sm text-orange-700">
              {error}
            </p>
            <p className="text-xs text-orange-600 mt-2">
              Note: This is a demonstration environment. LLM generation requires an OpenAI API key configuration.
            </p>
          </div>
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="space-y-6">
          {/* Answer */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <h2 className="text-lg font-semibold text-gray-900">HealthCompass Answer</h2>
            </div>
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{response.answer}</p>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2 text-sm text-gray-500">
              <CheckCircle className="h-4 w-4" />
              Grounded response from {response.chunks_used} sources
            </div>
          </div>

          {/* Sources */}
          {response.sources.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Sources</h2>
              <div className="space-y-3">
                {response.sources.map((source) => (
                  <div
                    key={source.chunk_id}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">
                          [{source.rank}] {source.source}
                        </p>
                        <p className="text-sm text-gray-600">
                          Chunk {source.chunk_index} · ID: {source.chunk_id}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded border border-gray-200">
                          {source.distance.toFixed(4)}
                        </span>
                        <button
                          onClick={() => toggleSaveSource(source.chunk_id)}
                          className={`p-2 rounded-lg transition-colors ${
                            savedSources.has(source.chunk_id)
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                          title="Save source"
                        >
                          <Bookmark className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AskHealthCompass;
