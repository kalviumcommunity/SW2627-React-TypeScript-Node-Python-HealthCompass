import { useState, useEffect } from 'react';
import { Bookmark, Trash2, BookOpen, Calendar, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getSavedGuidance, removeSavedGuidance, type SavedGuidanceItem } from '../api/client';

function SavedGuidance() {
  const navigate = useNavigate();
  const [savedItems, setSavedItems] = useState<SavedGuidanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSavedItems();
  }, []);

  const loadSavedItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await getSavedGuidance();
      setSavedItems(items);
    } catch (err) {
      console.error('Failed to load saved items:', err);
      setError('Failed to load saved guidance from server.');
    } finally {
      setLoading(false);
    }
  };

  const removeItem = async (id: string) => {
    try {
      await removeSavedGuidance(id);
      setSavedItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error('Failed to remove saved item:', err);
    }
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Saved Guidance</h1>
        <p className="text-sm text-gray-500">Guidance you've saved for quick access.</p>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-md">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <p className="text-sm text-gray-500">Loading saved guidance...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && savedItems.length === 0 && (
        <div className="text-center py-12">
          <Bookmark className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-sm text-gray-500">No saved guidance yet</p>
          <p className="text-xs text-gray-400 mt-2">
            Save guidance from the Guidance Library or Ask HealthCompass to access it here
          </p>
        </div>
      )}

      {/* Saved Items */}
      {!loading && savedItems.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {savedItems.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-gray-200 rounded-lg shadow-sm p-4"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center">
                  <BookOpen className="h-5 w-5 text-teal-600" />
                </div>
                <button
                  onClick={() => removeItem(item.id)}
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  title="Remove"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <h3 className="text-sm font-semibold text-gray-900 mb-1">{item.title}</h3>
              <p className="text-xs text-primary-700 font-medium mb-1">{item.topic}</p>
              <p className="text-xs text-gray-400 mb-2">{item.source}</p>
              {item.excerpt && (
                <p className="text-xs text-gray-600 line-clamp-2 bg-gray-50 p-2 rounded mb-3">
                  {item.excerpt}
                </p>
              )}
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Calendar className="h-3 w-3" />
                  <span>Saved {item.dateSaved}</span>
                </div>
                <button
                  onClick={() => navigate('/ask')}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                >
                  Consult Protocol <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SavedGuidance;
