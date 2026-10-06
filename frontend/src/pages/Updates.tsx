import { useState, useEffect } from 'react';
import { Calendar, Clock, ArrowRight, Search, Archive, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  getUpdates,
  getUpdateDetail,
  getUpdateDiff,
  markUpdateAsRead,
  ApiError,
  type PolicyUpdate,
  type UpdateCategory,
  type UpdateDiffResponse,
} from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { SearchInput } from '../components/ui/SearchInput';

function Updates() {
  const navigate = useNavigate();
  const [updates, setUpdates] = useState<PolicyUpdate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<UpdateCategory | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [diffModal, setDiffModal] = useState<{ update: PolicyUpdate | null; diff: UpdateDiffResponse | null }>({
    update: null,
    diff: null,
  });
  const [loadingDiff, setLoadingDiff] = useState(false);

  useEffect(() => {
    loadUpdates();
  }, [activeTab, searchQuery]);

  const loadUpdates = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { status: 'published' };
      if (activeTab !== 'all') {
        params.category = activeTab;
      }
      if (searchQuery) {
        params.search = searchQuery;
      }
      const response = await getUpdates(params);
      setUpdates(response.items);
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
    { id: 'all' as const, label: 'All Updates' },
    { id: 'outbreak' as const, label: 'Outbreak Directives' },
    { id: 'vaccination' as const, label: 'Vaccination' },
    { id: 'ppe' as const, label: 'PPE & Safety' },
  ];

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

  const handleCompareVersions = async (update: PolicyUpdate) => {
    setLoadingDiff(true);
    setDiffModal({ update, diff: null });
    try {
      const diff = await getUpdateDiff(update.id);
      setDiffModal({ update, diff });
    } catch (err) {
      console.error('Failed to load diff:', err);
    } finally {
      setLoadingDiff(false);
    }
  };

  const handleViewProtocol = (update: PolicyUpdate) => {
    // Mark as read when viewing
    if (!update.is_read) {
      markUpdateAsRead(update.id).catch(console.error);
      setUpdates((prev) =>
        prev.map((u) => (u.id === update.id ? { ...u, is_read: true } : u))
      );
    }
    // Navigate to document viewer (placeholder for now)
    console.log('View protocol:', update.document_id, update.new_version_id);
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

  const closeDiffModal = () => {
    setDiffModal({ update: null, diff: null });
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Updates & Policy Changes</h1>
        <p className="text-sm text-gray-500">
          Track official protocol updates, revision diffs, and circular amendments across District A facilities.
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <SearchInput
          placeholder="Search updates, protocols..."
          value={searchQuery}
          onChange={setSearchQuery}
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
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
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={loadUpdates}
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
            <Archive className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-sm font-medium text-gray-900 mb-1">No policy changes yet</h3>
          <p className="text-sm text-gray-500 mb-4">
            When guidance documents are revised, published changes will appear here.
          </p>
          <Button variant="outline" size="sm">
            View Guidance Library
          </Button>
        </Card>
      )}

      {/* Updates List */}
      {!loading && updates.length > 0 && (
        <div className="space-y-4">
          {updates.map((update) => (
            <Card
              key={update.id}
              className="p-5 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(`/updates/${update.id}`)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center">
                    <ArrowRight className="h-5 w-5 text-teal-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <Badge variant={getSeverityVariant(update.severity)}>
                        {update.severity}
                      </Badge>
                      <span className="text-xs text-gray-500 font-medium">
                        v{update.previous_version} → v{update.new_version}
                      </span>
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900">{update.title}</h3>
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
                <p className="text-sm text-gray-700 leading-relaxed">{update.summary}</p>
              </div>

              {/* Previous vs New */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 font-medium mb-2">PREVIOUS INSTRUCTION</p>
                  <p className="text-xs text-gray-600 italic line-clamp-3">{update.previous_instruction}</p>
                </div>
                <div className="bg-teal-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 font-medium mb-2">NEW DIRECTIVE</p>
                  <p className="text-xs text-gray-700 line-clamp-3">{update.new_instruction}</p>
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
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCompareVersions(update);
                    }}
                  >
                    Compare Versions
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewProtocol(update);
                    }}
                  >
                    View Protocol
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Archive Link */}
      {!loading && updates.length > 0 && (
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 mb-2">Looking for earlier revisions?</p>
          <p className="text-xs text-gray-400 mb-3">
            Access the complete immutable audit trail of clinical directives.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/updates/archive')}
          >
            <Archive className="h-4 w-4 mr-2" />
            Open Archive
          </Button>
        </div>
      )}

      {/* Diff Modal */}
      {diffModal.update && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-1">
                    {diffModal.update.document_title}
                  </h2>
                  <p className="text-sm text-gray-500">
                    Version {diffModal.update.previous_version} → Version {diffModal.update.new_version}
                  </p>
                </div>
                <button
                  onClick={closeDiffModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              {loadingDiff ? (
                <div className="text-center py-12">
                  <p className="text-sm text-gray-500">Loading diff...</p>
                </div>
              ) : diffModal.diff ? (
                <div className="space-y-6">
                  {/* Diff Summary */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-900 mb-2">Change Summary</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Total Changes</p>
                        <p className="font-semibold text-gray-900">{diffModal.diff.summary.total_changes}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Added</p>
                        <p className="font-semibold text-green-600">{diffModal.diff.summary.added_count}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Removed</p>
                        <p className="font-semibold text-red-600">{diffModal.diff.summary.removed_count}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Changed</p>
                        <p className="font-semibold text-gray-900">
                          {diffModal.diff.summary.change_percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Main Diff */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 mb-3">Main Instruction Change</h3>
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      {diffModal.diff.main_diff.map((change, idx) => (
                        <span
                          key={idx}
                          className={
                            change.type === 'added'
                              ? 'bg-green-100 text-green-800 px-1 rounded'
                              : change.type === 'removed'
                              ? 'bg-red-100 text-red-800 px-1 rounded line-through'
                              : 'text-gray-700'
                          }
                        >
                          {change.content}{' '}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Section Diffs */}
                  {diffModal.diff.section_diffs.map((sectionDiff, idx) => (
                    <div key={idx}>
                      <h3 className="text-sm font-medium text-gray-900 mb-3">{sectionDiff.section_name}</h3>
                      {sectionDiff.change_summary && (
                        <p className="text-xs text-gray-500 mb-2">{sectionDiff.change_summary}</p>
                      )}
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        {sectionDiff.diff.map((change, changeIdx) => (
                          <span
                            key={changeIdx}
                            className={
                              change.type === 'added'
                                ? 'bg-green-100 text-green-800 px-1 rounded'
                                : change.type === 'removed'
                                ? 'bg-red-100 text-red-800 px-1 rounded line-through'
                                : 'text-gray-700'
                            }
                          >
                            {change.content}{' '}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* Actions */}
                  <div className="flex justify-end gap-2 pt-4 border-t border-gray-100">
                    <Button variant="outline" size="sm" onClick={closeDiffModal}>
                      Close
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        handleViewProtocol(diffModal.update!);
                        closeDiffModal();
                      }}
                    >
                      View Full Protocol
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-sm text-gray-500">Failed to load diff</p>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

export default Updates;
