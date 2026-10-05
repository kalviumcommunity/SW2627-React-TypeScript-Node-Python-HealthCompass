import { useState, useEffect } from 'react';
import { Bookmark, Trash2, BookOpen, Calendar } from 'lucide-react';

interface SavedItem {
  id: string;
  title: string;
  topic: string;
  source: string;
  dateSaved: string;
}

function SavedGuidance() {
  const [savedItems, setSavedItems] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSavedItems();
  }, []);

  const loadSavedItems = () => {
    // Load from localStorage for demo purposes
    const saved = localStorage.getItem('savedGuidance');
    if (saved) {
      try {
        setSavedItems(JSON.parse(saved));
      } catch (err) {
        console.error('Failed to parse saved items:', err);
      }
    }
    setLoading(false);
  };

  const removeItem = (id: string) => {
    const updated = savedItems.filter((item) => item.id !== id);
    setSavedItems(updated);
    localStorage.setItem('savedGuidance', JSON.stringify(updated));
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Saved Guidance</h1>
        <p className="text-sm text-gray-500">Guidance you've saved for quick access.</p>
      </div>

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
              <h3 className="text-sm font-semibold text-gray-900 mb-2">{item.title}</h3>
              <p className="text-xs text-gray-500 mb-1">{item.topic}</p>
              <p className="text-xs text-gray-400 mb-3">{item.source}</p>
              <div className="flex items-center gap-1 text-xs text-gray-500 pt-3 border-t border-gray-100">
                <Calendar className="h-3 w-3" />
                <span>Saved {item.dateSaved}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SavedGuidance;
