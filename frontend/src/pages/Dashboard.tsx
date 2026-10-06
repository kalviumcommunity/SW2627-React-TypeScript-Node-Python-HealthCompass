import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  AlertTriangle,
  FileText,
  BookOpen,
  MessageSquare,
  Activity,
  RefreshCw,
  Shield,
  Search,
  Clock,
  MapPin,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { getDashboard, ApiError } from '../api/client';

// ─── Backend Response Types ──────────────────────────────────────

interface DashboardMetrics {
  totalGuidance: number;
  indexedGuidance: number;
  processingGuidance: number;
  failedGuidance: number;
  archivedGuidance: number;
  recentUpdates: number;
  criticalUpdates: number;
  activeAlerts: number;
}

interface GuidanceSummary {
  id: string;
  title: string;
  category: string;
  version: string;
  authority: string;
  region: string;
  effectiveDate: string;
  status: string;
  indexedAt: string | null;
}

interface UpdateSummary {
  id: string;
  title: string;
  category: string;
  severity: string;
  previousVersion: string;
  newVersion: string;
  effectiveDate: string;
  publishedAt: string;
  isRead: boolean;
}

interface CategoryCount {
  category: string;
  count: number;
}

interface KnowledgeBaseHealth {
  indexed: number;
  processing: number;
  failed: number;
  archived: number;
}

interface DashboardResponse {
  metrics: DashboardMetrics;
  recentGuidance: GuidanceSummary[];
  recentUpdates: UpdateSummary[];
  categoryCounts: CategoryCount[];
  knowledgeBaseHealth: KnowledgeBaseHealth;
}

// ─── User Profile (Static for now) ───────────────────────────────

const currentUser = {
  name: 'Sarah Jenkins',
  initials: 'SJ',
  role: 'Field Medical Officer',
  region: 'District A',
  department: 'Public Health',
};

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

const formattedDate = new Date().toLocaleDateString('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
});

// ─── Metric Card Component ───────────────────────────────────────

function MetricCard({
  icon: Icon,
  value,
  label,
  subtitle,
  href,
  accentColor,
  bgColor,
}: {
  icon: any;
  value: number;
  label: string;
  subtitle: string;
  href: string;
  accentColor: string;
  bgColor: string;
}) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(href)}
      className="w-full bg-white border border-gray-200 rounded-card p-4 shadow-card hover:shadow-md transition-shadow text-left"
    >
      <div className="flex items-start justify-between mb-2">
        <div className={`w-10 h-10 ${bgColor} rounded-lg flex items-center justify-center`}>
          <Icon className={`h-5 w-5 ${accentColor}`} />
        </div>
        <span className="text-xs text-gray-400">{formattedDate}</span>
      </div>
      <p className="text-2xl font-semibold text-navy-900 mb-1">{value}</p>
      <p className="text-sm font-medium text-gray-700 mb-0.5">{label}</p>
      <p className="text-xs text-gray-500">{subtitle}</p>
    </button>
  );
}

// ─── Main Dashboard Component ────────────────────────────────────

function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [askQuestion, setAskQuestion] = useState('');

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getDashboard();
      setData(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load dashboard data');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleAskSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (askQuestion.trim()) {
      navigate('/ask', { state: { question: askQuestion } });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'indexed':
        return 'text-green-600 bg-green-50';
      case 'processing':
        return 'text-amber-600 bg-amber-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      case 'archived':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium':
        return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="max-w-dashboard mx-auto px-6 py-6 lg:px-8 animate-fade-in">
        <div className="space-y-6">
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-card p-4 shadow-card animate-pulse">
                <div className="h-5 w-5 bg-gray-200 rounded mb-3" />
                <div className="h-7 w-12 bg-gray-200 rounded mb-1" />
                <div className="h-3 w-20 bg-gray-100 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-dashboard mx-auto px-6 py-6 lg:px-8 animate-fade-in">
        <div className="bg-red-50 border border-red-200 rounded-card p-6 text-center">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-red-900 mb-2">Unable to Load Dashboard</h3>
          <p className="text-sm text-red-700 mb-4">{error}</p>
          <button
            onClick={loadDashboard}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (!data) {
    return (
      <div className="max-w-dashboard mx-auto px-6 py-6 lg:px-8 animate-fade-in">
        <div className="bg-gray-50 border border-gray-200 rounded-card p-12 text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">No Data Available</h3>
          <p className="text-sm text-gray-500 mb-4">
            Upload guidance documents to populate the dashboard.
          </p>
          <button
            onClick={() => navigate('/guidance')}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go to Guidance Library
          </button>
        </div>
      </div>
    );
  }

  const metricCards = data.metrics.activeAlerts > 0 || data.metrics.failedGuidance > 0
    ? [
        {
          id: 'alerts',
          icon: AlertTriangle,
          value: data.metrics.activeAlerts,
          label: 'Critical Alerts',
          subtitle: data.metrics.criticalUpdates > 0
            ? `${data.metrics.criticalUpdates} critical updates`
            : 'No critical alerts',
          href: '/updates',
          accentColor: 'text-red-600',
          bgColor: 'bg-red-50',
        },
        {
          id: 'failed',
          icon: AlertCircle,
          value: data.metrics.failedGuidance,
          label: 'Failed Indexing',
          subtitle: 'Documents requiring attention',
          href: '/guidance?status=failed',
          accentColor: 'text-red-600',
          bgColor: 'bg-red-50',
        },
        {
          id: 'updates',
          icon: FileText,
          value: data.metrics.recentUpdates,
          label: 'Recent Updates',
          subtitle: 'Latest policy changes',
          href: '/updates',
          accentColor: 'text-amber-600',
          bgColor: 'bg-amber-50',
        },
        {
          id: 'guidance',
          icon: BookOpen,
          value: data.metrics.indexedGuidance,
          label: 'Active Guidance',
          subtitle: `${data.metrics.totalGuidance} total documents`,
          href: '/guidance',
          accentColor: 'text-primary-600',
          bgColor: 'bg-primary-50',
        },
      ]
    : [
        {
          id: 'guidance',
          icon: BookOpen,
          value: data.metrics.indexedGuidance,
          label: 'Active Guidance',
          subtitle: `${data.metrics.totalGuidance} total documents`,
          href: '/guidance',
          accentColor: 'text-primary-600',
          bgColor: 'bg-primary-50',
        },
        {
          id: 'updates',
          icon: FileText,
          value: data.metrics.recentUpdates,
          label: 'Recent Updates',
          subtitle: 'Latest policy changes',
          href: '/updates',
          accentColor: 'text-amber-600',
          bgColor: 'bg-amber-50',
        },
        {
          id: 'health',
          icon: Shield,
          value: data.metrics.indexedGuidance,
          label: 'Knowledge Base',
          subtitle: 'All documents indexed',
          href: '/guidance',
          accentColor: 'text-green-600',
          bgColor: 'bg-green-50',
        },
      ];

  return (
    <div className="max-w-dashboard mx-auto px-6 py-6 lg:px-8 animate-fade-in">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-navy-900 mb-0.5">
            {greeting()}, {currentUser.name.split(' ')[0]}.
          </h1>
          <p className="text-sm text-gray-500">
            {currentUser.region} • {currentUser.department}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400 hidden sm:block">{formattedDate}</span>
          <button
            onClick={loadDashboard}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Refresh dashboard"
          >
            <RefreshCw className="h-4.5 w-4.5" />
          </button>
        </div>
      </div>

      {/* ── Ask HealthCompass Quick Search ──────────────────── */}
      <div className="bg-white border border-gray-200 rounded-card shadow-card p-5 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare className="h-5 w-5 text-primary-600" />
          <h2 className="text-sm font-semibold text-navy-900">Ask HealthCompass</h2>
        </div>
        <form onSubmit={handleAskSubmit}>
          <div className="relative mb-3">
            <input
              type="text"
              value={askQuestion}
              onChange={(e) => setAskQuestion(e.target.value)}
              placeholder="Ask about isolation, vaccination, PPE, outbreaks, or any approved guidance..."
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-shadow"
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="flex gap-2 flex-wrap">
              {['Isolation guidance', 'Vaccination guidance', 'PPE guidance'].map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setAskQuestion(suggestion)}
                  className="text-xs px-2.5 py-1 bg-gray-100 text-gray-600 rounded-md hover:bg-primary-50 hover:text-primary-700 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
            <button
              type="submit"
              disabled={!askQuestion.trim()}
              className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              Ask <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </form>
      </div>

      {/* ── Metric Cards ───────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {metricCards.map((card) => (
          <MetricCard key={card.id} {...card} />
        ))}
      </div>

      {/* ── Main Content Grid ──────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Left: Recent Guidance */}
        <div className="bg-white border border-gray-200 rounded-card shadow-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-primary-600" />
              <h2 className="text-sm font-semibold text-navy-900">Current Guidance</h2>
            </div>
            <button
              onClick={() => navigate('/guidance')}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
            >
              View all <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          {data.recentGuidance.length > 0 ? (
            <div className="space-y-3">
              {data.recentGuidance.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-navy-900 leading-tight mb-1 truncate">
                        {doc.title}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span className={`px-1.5 py-0.5 rounded ${getStatusColor(doc.status)}`}>
                          {doc.status}
                        </span>
                        <span>•</span>
                        <span>{doc.category}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {doc.region}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {doc.effectiveDate}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No guidance documents yet</p>
            </div>
          )}
        </div>

        {/* Right: Recent Updates */}
        <div className="bg-white border border-gray-200 rounded-card shadow-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-amber-600" />
              <h2 className="text-sm font-semibold text-navy-900">Recent Updates</h2>
            </div>
            <button
              onClick={() => navigate('/updates')}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
            >
              View all <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          {data.recentUpdates.length > 0 ? (
            <div className="space-y-3">
              {data.recentUpdates.map((update) => (
                <div
                  key={update.id}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-navy-900 leading-tight mb-1 truncate">
                        {update.title}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span className={`px-1.5 py-0.5 rounded border ${getSeverityColor(update.severity)}`}>
                          {update.severity}
                        </span>
                        <span>•</span>
                        <span>{update.category}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>
                      v{update.previousVersion} → v{update.newVersion}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {update.effectiveDate}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No recent updates</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Second Row: Knowledge Base Health & Categories ──── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Knowledge Base Health */}
        <div className="bg-white border border-gray-200 rounded-card shadow-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="h-5 w-5 text-green-600" />
            <h2 className="text-sm font-semibold text-navy-900">Knowledge Base Health</h2>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-gray-700">Indexed</span>
              </div>
              <span className="text-sm font-semibold text-green-600">
                {data.knowledgeBaseHealth.indexed}
              </span>
            </div>

            {data.knowledgeBaseHealth.processing > 0 && (
              <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 text-amber-600 animate-spin" />
                  <span className="text-sm font-medium text-gray-700">Processing</span>
                </div>
                <span className="text-sm font-semibold text-amber-600">
                  {data.knowledgeBaseHealth.processing}
                </span>
              </div>
            )}

            {data.knowledgeBaseHealth.failed > 0 && (
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg cursor-pointer hover:bg-red-100 transition-colors"
                onClick={() => navigate('/guidance?status=failed')}
              >
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium text-gray-700">Failed</span>
                </div>
                <span className="text-sm font-semibold text-red-600">
                  {data.knowledgeBaseHealth.failed}
                </span>
              </div>
            )}

            {data.knowledgeBaseHealth.archived > 0 && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700">Archived</span>
                </div>
                <span className="text-sm font-semibold text-gray-600">
                  {data.knowledgeBaseHealth.archived}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Guidance by Category */}
        <div className="bg-white border border-gray-200 rounded-card shadow-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Search className="h-5 w-5 text-primary-600" />
            <h2 className="text-sm font-semibold text-navy-900">Guidance by Category</h2>
          </div>

          {data.categoryCounts.length > 0 ? (
            <div className="space-y-2">
              {data.categoryCounts.map((cat) => (
                <div
                  key={cat.category}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => navigate(`/guidance?category=${encodeURIComponent(cat.category)}`)}
                >
                  <span className="text-sm font-medium text-gray-700">{cat.category}</span>
                  <span className="text-sm font-semibold text-primary-600">{cat.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Search className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No categories found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
