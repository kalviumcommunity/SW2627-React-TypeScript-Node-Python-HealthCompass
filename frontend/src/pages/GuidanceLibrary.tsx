import { useState, useEffect } from 'react';
import { Search, Bookmark } from 'lucide-react';
import { getGuidance, searchGuidance, ApiError } from '../api/client';
import type { GuidanceItem } from '../api/client';

function GuidanceLibrary() {
  const [guidance, setGuidance] = useState<GuidanceItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savedItems, setSavedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadGuidance();
  }, []);

  const loadGuidance = async () => {
    try {
      const data = await getGuidance();
      setGuidance(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load guidance');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadGuidance();
      return;
    }

    try {
      const data = await searchGuidance(searchQuery);
      setGuidance(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Search failed');
      }
    }
  };

  const toggleSave = (id: string) => {
    const newSaved = new Set(savedItems);
    if (newSaved.has(id)) {
      newSaved.delete(id);
    } else {
      newSaved.add(id);
    }
    setSavedItems(newSaved);
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Guidance Library</h1>
        <p className="text-gray-600">
          Search and browse official public health guidance documents
        </p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search guidance by topic, title, or description..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-center py-12">
          <p className="text-gray-500">Loading guidance...</p>
        </div>
      )}

      {/* Guidance list */}
      {!loading && guidance.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No guidance found</p>
        </div>
      )}

      {!loading && guidance.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {guidance.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                  {item.topic}
                </span>
                <button
                  onClick={() => toggleSave(item.id)}
                  className={`p-2 rounded-lg transition-colors ${
                    savedItems.has(item.id)
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <Bookmark className="h-4 w-4" />
                </button>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
              <p className="text-sm text-gray-600 mb-4">{item.description}</p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{item.source}</span>
                <span>Updated {item.last_updated}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default GuidanceLibrary;
