import { useState, useEffect } from 'react';
import { Calendar, TrendingUp } from 'lucide-react';
import { getUpdates, ApiError } from '../api/client';
import type { UpdateItem } from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

function Updates() {
  const [updates, setUpdates] = useState<UpdateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');

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

  const tabs = [
    { id: 'all', label: 'All Updates' },
    { id: 'outbreak', label: 'Outbreak Directives' },
    { id: 'vaccination', label: 'Vaccination' },
    { id: 'ppe', label: 'PPE & Safety' },
  ];

  const getImportanceVariant = (importance: string) => {
    switch (importance.toLowerCase()) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'info';
    }
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Updates & Policy Changes</h1>
        <p className="text-sm text-gray-500">Track official protocol updates, revision differences, and circular amendments.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-teal-600 text-white'
                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <Card className="p-4 mb-6 border-l-4 border-l-orange-400 bg-orange-50">
          <p className="text-sm text-orange-700">{error}</p>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <p className="text-sm text-gray-500">Loading updates...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && updates.length === 0 && (
        <div className="text-center py-12">
          <p className="text-sm text-gray-500">No recent updates</p>
        </div>
      )}

      {/* Updates List */}
      {!loading && updates.length > 0 && (
        <div className="space-y-4">
          {updates.map((update) => (
            <Card key={update.id} className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 text-teal-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={getImportanceVariant(update.importance)}>
                        {update.importance}
                      </Badge>
                      <span className="text-xs text-gray-500">v4.1 → v4.2</span>
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900">{update.title}</h3>
                  </div>
                </div>
                <Badge variant="active">PUBLISHED</Badge>
              </div>

              <div className="mb-4">
                <p className="text-xs text-gray-500 mb-2">Previous instruction:</p>
                <p className="text-xs text-gray-400 italic">[Previous version content would appear here]</p>
              </div>

              <div className="mb-4">
                <p className="text-xs text-gray-500 mb-2">Updated instruction:</p>
                <p className="text-xs text-gray-700">{update.summary}</p>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Calendar className="h-3 w-3" />
                  <span>Published {update.date}</span>
                </div>
                <button className="text-xs text-teal-600 hover:text-teal-700 font-medium">
                  View Details →
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default Updates;
