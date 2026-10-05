import { useState, useEffect } from 'react';
import { Search, Bookmark, Filter, ExternalLink } from 'lucide-react';
import { getGuidance, searchGuidance, ApiError } from '../api/client';
import type { GuidanceItem } from '../api/client';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { SearchInput } from '../components/ui/SearchInput';

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
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Guidance Library</h1>
        <p className="text-sm text-gray-500">Official health guidelines, vaccination protocols, and advisories.</p>
      </div>

      {/* Toolbar */}
      <Card className="p-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <SearchInput
              placeholder="Search guidelines, topics, or circular keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <Button variant="secondary" onClick={handleSearch}>
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
          <Button variant="ghost">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button variant="ghost" onClick={loadGuidance}>
            Reset
          </Button>
        </div>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="p-4 mb-6 border-l-4 border-l-orange-400 bg-orange-50">
          <p className="text-sm text-orange-700">{error}</p>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <p className="text-sm text-gray-500">Loading guidance...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && guidance.length === 0 && (
        <div className="text-center py-12">
          <p className="text-sm text-gray-500">No guidance found</p>
        </div>
      )}

      {/* Guidance Grid */}
      {!loading && guidance.length > 0 && (
        <>
          <p className="text-xs text-gray-500 mb-4">Showing {guidance.length} protocols</p>
          <div className="grid grid-cols-3 gap-4">
            {guidance.map((item) => (
              <div key={item.id} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer p-4">
                <div className="flex items-start justify-between mb-3">
                  <Badge variant="active">ACTIVE</Badge>
                  <button
                    onClick={() => toggleSave(item.id)}
                    className={`p-1.5 rounded-md transition-colors ${
                      savedItems.has(item.id)
                        ? 'bg-teal-100 text-teal-600'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <Bookmark className={`h-4 w-4 ${savedItems.has(item.id) ? 'fill-current' : ''}`} />
                  </button>
                </div>
                <p className="text-xs text-gray-400 mb-2">{item.last_updated}</p>
                <h3 className="text-sm font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-xs text-gray-500 mb-1">{item.source}</p>
                <p className="text-xs text-gray-400 mb-3">District A</p>
                <p className="text-xs text-gray-600 mb-4 line-clamp-2">{item.description}</p>
                <Button variant="ghost" className="w-full text-xs">
                  Read Protocol
                  <ExternalLink className="h-3 w-3 ml-2" />
                </Button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default GuidanceLibrary;
