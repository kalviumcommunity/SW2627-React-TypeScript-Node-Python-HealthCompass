import { useState, useEffect } from 'react';
import { Calendar, Clock, ArrowRight, ChevronLeft } from 'lucide-react';
import {
  getArchivedUpdates,
  ApiError,
  type PolicyUpdate,
} from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useNavigate } from 'react-router-dom';

function Archive() {
  const navigate = useNavigate();
  const [updates, setUpdates] = useState<PolicyUpdate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadArchivedUpdates();
  }, [page]);

  const loadArchivedUpdates = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getArchivedUpdates({ page, page_size: 10 });
      setUpdates(response.items);
      setTotal(response.total);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load archived updates');
      }
    } finally {
      setLoading(false);
    }
  };

  const getSeverityVariant = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'info';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(dateString);
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/updates')}
          className="mb-4"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Updates
        </Button>
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Archive</h1>
        <p className="text-sm text-gray-500">
          Access the complete immutable audit trail of clinical directives and historical policy changes.
        </p>
      </div>

      {/* Error State */}
      {error && (
        <Card className="p-4 mb-6 border-l-4 border-l-orange-400 bg-orange-50">
          <p className="text-sm text-orange-700">{error}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={loadArchivedUpdates}
          >
            Retry
          </Button>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg animate-pulse" />
                  <div className="space-y-2">
                    <div className="h-4 w-24 bg-gray-100 rounded animate-pulse" />
                    <div className="h-4 w-64 bg-gray-100 rounded animate-pulse" />
                  </div>
                </div>
                <div className="h-6 w-20 bg-gray-100 rounded animate-pulse" />
              </div>
              <div className="space-y-2 mb-4">
                <div className="h-3 w-full bg-gray-100 rounded animate-pulse" />
                <div className="h-3 w-3/4 bg-gray-100 rounded animate-pulse" />
              </div>
              <div className="h-px bg-gray-100" />
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && updates.length === 0 && (
        <Card className="p-12 text-center">
          <div className="text-gray-400 mb-4">
            <Calendar className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-sm font-medium text-gray-900 mb-1">No archived updates</h3>
          <p className="text-sm text-gray-500 mb-4">
            Historical policy changes will appear here when they are archived.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/updates')}
          >
            View Current Updates
          </Button>
        </Card>
      )}

      {/* Updates List */}
      {!loading && updates.length > 0 && (
        <>
          <div className="space-y-4">
            {updates.map((update) => (
              <Card key={update.id} className="p-5 opacity-75">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                      <ArrowRight className="h-5 w-5 text-gray-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <Badge variant={getSeverityVariant(update.severity)}>
                          {update.severity}
                        </Badge>
                        <Badge variant="active">ARCHIVED</Badge>
                        <span className="text-xs text-gray-500 font-medium">
                          v{update.previous_version} → v{update.new_version}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-gray-700">{update.title}</h3>
                    </div>
                  </div>
                  {update.effective_date && (
                    <div className="text-xs text-gray-500 flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>Effective {formatDate(update.effective_date)}</span>
                    </div>
                  )}
                </div>

                {/* Summary */}
                <div className="mb-4">
                  <p className="text-sm text-gray-600 leading-relaxed">{update.summary}</p>
                </div>

                {/* Previous vs New */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 font-medium mb-2">PREVIOUS INSTRUCTION</p>
                    <p className="text-xs text-gray-500 italic line-clamp-3">{update.previous_instruction}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 font-medium mb-2">NEW DIRECTIVE</p>
                    <p className="text-xs text-gray-600 line-clamp-3">{update.new_instruction}</p>
                  </div>
                </div>

                {/* Published Info */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="h-3 w-3" />
                    <span>
                      Published {formatRelativeTime(update.published_at)}
                      {update.published_by && ` by ${update.published_by}`}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {total > 10 && (
            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-gray-500">
                Showing {((page - 1) * 10) + 1}-{Math.min(page * 10, total)} of {total} archived updates
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page * 10 >= total}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Archive;
