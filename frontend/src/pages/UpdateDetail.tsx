import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Calendar,
  Clock,
  ChevronLeft,
  FileText,
  ArrowRight,
  AlertCircle,
  Info,
} from 'lucide-react';
import {
  getUpdateDetail,
  getDocumentVersions,
  getUpdateDiff,
  markUpdateAsRead,
  ApiError,
  type PolicyUpdate,
  type DocumentVersion,
  type UpdateDiffResponse,
} from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

function UpdateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [update, setUpdate] = useState<PolicyUpdate | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [diff, setDiff] = useState<UpdateDiffResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingDiff, setLoadingDiff] = useState(false);

  useEffect(() => {
    if (id) {
      loadUpdateData(id);
    }
  }, [id]);

  const loadUpdateData = async (updateId: string) => {
    setLoading(true);
    setError(null);
    try {
      const updateData = await getUpdateDetail(updateId);
      setUpdate(updateData);

      // Load versions after we have the update data
      try {
        const versionsData = await getDocumentVersions(updateData.document_id);
        setVersions(versionsData.versions || []);
      } catch (err) {
        console.error('Failed to load versions:', err);
        setVersions([]);
      }

      // Mark as read
      if (!updateData.is_read) {
        markUpdateAsRead(updateId).catch(console.error);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load update details');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadDiff = async () => {
    if (!update) return;
    setLoadingDiff(true);
    try {
      const diffData = await getUpdateDiff(update.id);
      setDiff(diffData);
    } catch (err) {
      console.error('Failed to load diff:', err);
    } finally {
      setLoadingDiff(false);
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
    return date.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });
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

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 w-64 bg-gray-200 rounded" />
            <div className="h-4 w-full bg-gray-200 rounded" />
            <div className="h-32 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !update) {
    return (
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <Card className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Update</h3>
            <p className="text-sm text-gray-500 mb-4">{error || 'Update not found'}</p>
            <Button variant="outline" size="sm" onClick={() => navigate('/updates')}>
              Back to Updates
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
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
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <Badge variant={getSeverityVariant(update.severity)}>
                  {update.severity}
                </Badge>
                <Badge variant="active">PUBLISHED</Badge>
                <span className="text-sm text-gray-500 font-medium">
                  v{update.previous_version} → v{update.new_version}
                </span>
              </div>
              <h1 className="text-2xl font-semibold text-gray-900 mb-2">{update.title}</h1>
              <p className="text-sm text-gray-500">{update.document_title}</p>
            </div>
          </div>
        </div>

        {/* Metadata */}
        <Card className="p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                <Calendar className="h-4 w-4" />
                <span>Effective Date</span>
              </div>
              <p className="text-sm font-medium text-gray-900">
                {update.effective_date ? formatDate(update.effective_date) : 'Not specified'}
              </p>
            </div>
            <div>
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                <Clock className="h-4 w-4" />
                <span>Published</span>
              </div>
              <p className="text-sm font-medium text-gray-900">
                {formatRelativeTime(update.published_at)}
                {update.published_by && ` by ${update.published_by}`}
              </p>
            </div>
            {update.authority && (
              <div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                  <Info className="h-4 w-4" />
                  <span>Authority</span>
                </div>
                <p className="text-sm font-medium text-gray-900">{update.authority}</p>
              </div>
            )}
            {update.region && (
              <div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                  <FileText className="h-4 w-4" />
                  <span>Region</span>
                </div>
                <p className="text-sm font-medium text-gray-900">{update.region}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Summary */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Summary</h2>
          <p className="text-sm text-gray-700 leading-relaxed">{update.summary}</p>
        </Card>

        {/* Change Summary */}
        {update.change_reason && (
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Why It Changed</h2>
            <p className="text-sm text-gray-700 leading-relaxed">{update.change_reason}</p>
          </Card>
        )}

        {/* Impact */}
        {update.impact && (
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Impact</h2>
            <p className="text-sm text-gray-700 leading-relaxed">{update.impact}</p>
          </Card>
        )}

        {/* What Changed */}
        <Card className="p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">What Changed</h2>
            {!diff && (
              <Button variant="outline" size="sm" onClick={loadDiff} disabled={loadingDiff}>
                {loadingDiff ? 'Loading...' : 'Show Diff'}
              </Button>
            )}
          </div>

          {/* Main Instruction Change */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Main Instruction</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs text-gray-500 font-medium mb-2">PREVIOUS</p>
                <p className="text-sm text-gray-600 italic">{update.previous_instruction}</p>
              </div>
              <div className="bg-teal-50 rounded-lg p-4">
                <p className="text-xs text-gray-500 font-medium mb-2">NEW</p>
                <p className="text-sm text-gray-700">{update.new_instruction}</p>
              </div>
            </div>
          </div>

          {/* Diff View */}
          {diff && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Change Summary</h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Total Changes</p>
                    <p className="font-semibold text-gray-900">{diff.summary.total_changes}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Added</p>
                    <p className="font-semibold text-green-600">{diff.summary.added_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Removed</p>
                    <p className="font-semibold text-red-600">{diff.summary.removed_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Changed</p>
                    <p className="font-semibold text-gray-900">
                      {diff.summary.change_percentage.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                {diff.main_diff.map((change, idx) => (
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
          )}

          {/* Changed Sections */}
          {update.changed_sections.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Changed Sections</h3>
              {update.changed_sections.map((section, idx) => (
                <div key={idx} className="mb-4 last:mb-0">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">{section.section_name}</h4>
                  {section.change_summary && (
                    <p className="text-xs text-gray-500 mb-2">{section.change_summary}</p>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 font-medium mb-1">PREVIOUS</p>
                      <p className="text-xs text-gray-600 italic line-clamp-3">{section.previous_content}</p>
                    </div>
                    <div className="bg-teal-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 font-medium mb-1">NEW</p>
                      <p className="text-xs text-gray-700 line-clamp-3">{section.new_content}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Version History */}
        {versions.length > 0 && (
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Version History</h2>
            <div className="space-y-3">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    version.id === update.new_version_id
                      ? 'bg-teal-50 border border-teal-200'
                      : 'bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white">
                      <FileText className="h-4 w-4 text-gray-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {version.version}
                        {version.id === update.new_version_id && (
                          <span className="ml-2 text-xs text-teal-600 font-medium">(Current)</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500">
                        {version.published_date ? formatDate(version.published_date) : 'No date'}
                      </p>
                    </div>
                  </div>
                  <Badge variant={version.status === 'active' ? 'active' : 'info'}>
                    {version.status}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <Button variant="primary" size="md">
            <FileText className="h-4 w-4 mr-2" />
            View Current Protocol
          </Button>
          {update.previous_version_id && (
            <Button variant="outline" size="md">
              <ArrowRight className="h-4 w-4 mr-2" />
              View Previous Version
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export default UpdateDetail;
