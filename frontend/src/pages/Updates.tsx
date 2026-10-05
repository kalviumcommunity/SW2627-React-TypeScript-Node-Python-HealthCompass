import { useState, useEffect } from 'react';
import { FileText, Calendar } from 'lucide-react';
import { getUpdates, ApiError } from '../api/client';
import type { UpdateItem } from '../api/client';

function Updates() {
  const [updates, setUpdates] = useState<UpdateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUpdates();
  }, []);

  const loadUpdates = async () => {
    try {
      const data = await getUpdates();
      setUpdates(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load updates');
      }
    } finally {
      setLoading(false);
    }
  };

  const getImportanceColor = (importance: string) => {
    switch (importance.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-blue-100 text-blue-700 border-blue-200';
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Updates & Policy Changes</h1>
        <p className="text-gray-600">
          Recent policy updates and guidance changes
        </p>
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
          <p className="text-gray-500">Loading updates...</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && updates.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No recent updates</p>
        </div>
      )}

      {/* Updates list */}
      {!loading && updates.length > 0 && (
        <div className="space-y-4">
          {updates.map((update) => (
            <div
              key={update.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileText className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{update.title}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span>{update.category}</span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {update.date}
                      </span>
                    </div>
                  </div>
                </div>
                <span
                  className={`text-xs font-medium px-2 py-1 rounded ${getImportanceColor(
                    update.importance
                  )}`}
                >
                  {update.importance}
                </span>
              </div>
              <p className="text-gray-700 mb-4">{update.summary}</p>
              <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                Read more →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Updates;
