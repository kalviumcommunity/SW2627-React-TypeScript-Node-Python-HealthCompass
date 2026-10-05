import { useState, useEffect, useCallback } from 'react';
import {
  ArrowRight,
  AlertTriangle,
  FileText,
  BookOpen,
  MessageSquare,
  Activity,
  Users,
  ClipboardList,
  Bookmark,
  RefreshCw,
  Shield,
  Bell,
  AlertCircle,
  Search,
  TrendingUp,
  ChevronRight,
  Clock,
  MapPin,
  CheckCircle2,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// ─── Backend Response Types ──────────────────────────────────────

interface DashboardMetrics {
  activeAlerts: number;
  activeAlertsSubtitle: string;
  newGuidance: number;
  newGuidanceSubtitle: string;
  policyUpdates: number;
  policyUpdatesSubtitle: string;
  savedGuidance: number;
  savedGuidanceSubtitle: string;
}

interface DistrictItem {
  id: string;
  name: string;
  code: string;
  status: string;
  complianceRate: number;
  activeCases: number;
  alertsCount: number;
  reportingUnit: string;
  lastCheckIn: string;
}

interface BackendDistrictStatus {
  activeMobileUnits: number;
  totalCases: number;
  protocolAdoption: number;
  currentPpeTier: string;
  reportingCompliance: number;
  districts: DistrictItem[];
}

interface BackendActiveDirective {
  id: string;
  code: string;
  title: string;
  authority: string;
  region: string;
  severity: string;
  effectiveDate: string;
  reviewDate: string;
  summary: string;
  actionItems: string[];
  documentId: string | null;
}

interface FieldDirective {
  id: string;
  code: string;
  title: string;
  authority: string;
  region: string;
  urgency: string;
  publishedAt: string;
  category: string;
  summary: string;
  documentId: string | null;
}

interface BackendActivityItem {
  id: string;
  title: string;
  actor: string;
  action: string;
  category: string;
  timestamp: string;
  icon: string;
  documentId: string | null;
}

interface QuickTopic {
  id: string;
  name: string;
  count: number;
  category: string;
  description: string;
}

interface TrendPoint {
  date: string;
  day: string;
  cases: number;
  tests: number;
  discharges: number;
}

interface DashboardData {
  metrics: DashboardMetrics;
  districtStatus: BackendDistrictStatus;
  activeDirective: BackendActiveDirective;
  directives: FieldDirective[];
  recentActivity: BackendActivityItem[];
  quickTopics: QuickTopic[];
  trend: TrendPoint[];
}

// ─── Icon Lookup ─────────────────────────────────────────────────

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  ClipboardList,
  Shield,
  AlertTriangle,
  Activity,
  FileText,
  RefreshCw,
  Bookmark,
  Users,
  BookOpen,
  MessageSquare,
  CheckCircle2,
};

function getIcon(name: string) {
  return iconMap[name] || FileText;
}

// ─── User Profile (local) ────────────────────────────────────────

const currentUser = {
  name: 'Sarah Jenkins',
  role: 'Field Medical Officer',
  region: 'District A',
  department: 'Field Operations',
};

// ─── Suggested Questions ─────────────────────────────────────────

const suggestedQuestions = [
  'Isolation protocol',
  'Vaccination interval',
  'District PPE rules',
];

// ─── Dashboard ───────────────────────────────────────────────────

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [now] = useState(() => new Date());

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/dashboard`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const json: DashboardData = await res.json();
      setData(json);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleQuickAsk = () => {
    if (query.trim()) {
      navigate('/ask', { state: { question: query } });
    }
  };

  const handleSuggestedQuery = (question: string) => {
    navigate('/ask', { state: { question } });
  };

  const handleTopicClick = (topic: QuickTopic) => {
    navigate('/ask', { state: { question: topic.name } });
  };

  const greeting = () => {
    const h = now.getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const formattedDate = now.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  // ─── Severity & Status Colors ───────────────────────────────

  const severityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return { bg: 'bg-red-100', text: 'text-red-700', dot: 'bg-red-500' };
      case 'elevated': return { bg: 'bg-amber-100', text: 'text-amber-700', dot: 'bg-amber-500' };
      default: return { bg: 'bg-green-100', text: 'text-green-700', dot: 'bg-green-500' };
    }
  };

  const urgencyColor = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case 'critical': return { badge: 'bg-red-100 text-red-700', icon: 'text-red-500' };
      case 'routine': return { badge: 'bg-green-100 text-green-700', icon: 'text-green-500' };
      case 'advisory': return { badge: 'bg-blue-100 text-blue-700', icon: 'text-blue-500' };
      default: return { badge: 'bg-gray-100 text-gray-600', icon: 'text-gray-400' };
    }
  };

  const districtStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'critical': return { bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500' };
      case 'alert': return { bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-500' };
      default: return { bg: 'bg-green-50', border: 'border-green-200', dot: 'bg-green-500' };
    }
  };

  // ─── Metric Cards ───────────────────────────────────────────

  const metricCards = data
    ? [
        {
          id: 'alerts',
          icon: Activity,
          value: data.metrics.activeAlerts,
          label: 'Active Alerts',
          subtitle: data.metrics.activeAlertsSubtitle,
          href: '/alerts',
          accentColor: 'text-red-600',
          bgColor: 'bg-red-50',
        },
        {
          id: 'guidance',
          icon: BookOpen,
          value: data.metrics.newGuidance,
          label: 'New Guidance',
          subtitle: data.metrics.newGuidanceSubtitle,
          href: '/guidance',
          accentColor: 'text-primary-600',
          bgColor: 'bg-primary-50',
        },
        {
          id: 'updates',
          icon: FileText,
          value: data.metrics.policyUpdates,
          label: 'Policy Updates',
          subtitle: data.metrics.policyUpdatesSubtitle,
          href: '/updates',
          accentColor: 'text-amber-600',
          bgColor: 'bg-amber-50',
        },
        {
          id: 'saved',
          icon: Bookmark,
          value: data.metrics.savedGuidance,
          label: 'Saved Guidance',
          subtitle: data.metrics.savedGuidanceSubtitle,
          href: '/saved',
          accentColor: 'text-indigo-600',
          bgColor: 'bg-indigo-50',
        },
      ]
    : [];

  // ─── Error State ────────────────────────────────────────────

  if (error && !data) {
    return (
      <div className="max-w-dashboard mx-auto px-6 py-6 lg:px-8 animate-fade-in">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-semibold text-navy-900 mb-0.5">
              {greeting()}, {currentUser.name.split(' ')[0]}.
            </h1>
            <p className="text-sm text-gray-500">
              {currentUser.region} • {currentUser.department}
            </p>
          </div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-card p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-orange-900 mb-1">
                Unable to Load Dashboard
              </h3>
              <p className="text-sm text-orange-700 mb-3">{error}</p>
              <button
                onClick={loadDashboard}
                className="text-xs font-medium text-orange-700 hover:text-orange-900 flex items-center gap-1"
              >
                <RefreshCw className="h-3 w-3" /> Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
            className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Notifications"
          >
            <Bell className="h-4.5 w-4.5" />
            {data && data.metrics.activeAlerts > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
            )}
          </button>
        </div>
      </div>

      {/* ── Metric Cards ───────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-card p-4 shadow-card animate-pulse">
              <div className="h-5 w-5 bg-gray-200 rounded mb-3" />
              <div className="h-7 w-12 bg-gray-200 rounded mb-1" />
              <div className="h-3 w-20 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {metricCards.map((card) => (
            <button
              key={card.id}
              onClick={() => navigate(card.href)}
              className="bg-white border border-gray-200 rounded-card p-4 shadow-card hover:shadow-card-hover transition-all duration-200 text-left group focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label={`${card.label}: ${card.value}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className={`p-1.5 rounded-md ${card.bgColor}`}>
                  <card.icon className={`h-4 w-4 ${card.accentColor}`} />
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <p className="text-2xl font-semibold text-navy-900 mb-0.5">{card.value}</p>
              <p className="text-xs text-gray-500">{card.label}</p>
              {card.subtitle && (
                <p className="text-[11px] text-gray-400 mt-0.5">{card.subtitle}</p>
              )}
            </button>
          ))}
        </div>
      )}

      {/* ── Clinical Guidance Assistant ─────────────────────── */}
      <div className="bg-white border border-gray-200 rounded-card p-5 shadow-card mb-6">
        <div className="flex items-center gap-2 mb-1">
          <div className="p-1.5 rounded-md bg-primary-50">
            <MessageSquare className="h-4 w-4 text-primary-600" />
          </div>
          <h2 className="text-section-title text-navy-900">Clinical Guidance Assistant</h2>
        </div>
        <p className="text-sm text-gray-500 mb-4 ml-9">
          Find trusted public-health guidance in seconds.
        </p>
        <div className="flex gap-3 mb-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuickAsk()}
              placeholder="Search public health protocols, prevention guidance, or field procedures..."
              className="w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-shadow"
              aria-label="Search guidance"
            />
          </div>
          <button
            onClick={handleQuickAsk}
            disabled={!query.trim()}
            className="px-4 py-2.5 bg-primary-600 text-white text-sm font-medium rounded-button hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <Search className="h-4 w-4" />
            Ask HealthCompass
          </button>
        </div>
        <div className="flex gap-2 flex-wrap">
          {suggestedQuestions.map((chip) => (
            <button
              key={chip}
              onClick={() => handleSuggestedQuery(chip)}
              className="text-xs px-3 py-1.5 bg-gray-100 text-gray-600 rounded-button hover:bg-primary-50 hover:text-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* ── Active Directive (from backend) ─────────────────── */}
      {data && (
        <div className="bg-white border border-gray-200 rounded-card shadow-card mb-6 border-l-4 border-l-primary-600 overflow-hidden">
          <div className="p-4 flex items-start gap-3">
            <div className="w-9 h-9 bg-primary-50 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
              <AlertTriangle className="h-4.5 w-4.5 text-primary-600" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide ${severityColor(data.activeDirective.severity).bg} ${severityColor(data.activeDirective.severity).text}`}>
                  <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${severityColor(data.activeDirective.severity).dot}`} />
                  {data.activeDirective.severity}
                </span>
                <span className="text-xs text-gray-400">{data.activeDirective.region}</span>
                <span className="text-xs text-gray-300 hidden sm:inline">•</span>
                <span className="text-xs text-gray-400 hidden sm:inline font-mono">{data.activeDirective.code}</span>
              </div>
              <h3 className="text-sm font-semibold text-navy-900 mb-1">{data.activeDirective.title}</h3>
              <p className="text-xs text-gray-600 leading-relaxed mb-2">{data.activeDirective.summary}</p>
              {data.activeDirective.actionItems.length > 0 && (
                <div className="mb-2">
                  <ul className="space-y-1">
                    {data.activeDirective.actionItems.slice(0, 2).map((item, idx) => (
                      <li key={idx} className="text-[11px] text-gray-500 flex items-start gap-1.5">
                        <CheckCircle2 className="h-3 w-3 text-primary-500 mt-0.5 flex-shrink-0" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => navigate('/updates')}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 transition-colors"
                >
                  Review Updates
                  <ArrowRight className="h-3 w-3" />
                </button>
                <button
                  onClick={() => navigate('/guidance')}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 transition-colors"
                >
                  View Protocol
                  <ArrowRight className="h-3 w-3" />
                </button>
                {data.activeDirective.documentId && (
                  <button
                    onClick={() => navigate('/ask', { state: { question: data.activeDirective.title } })}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 transition-colors"
                  >
                    Ask About This
                    <MessageSquare className="h-3 w-3" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Loading Skeleton for Grid ──────────────────────── */}
      {loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-card p-4 shadow-card animate-pulse">
                <div className="h-3 w-16 bg-gray-200 rounded mb-2" />
                <div className="h-4 w-48 bg-gray-200 rounded mb-1" />
                <div className="h-3 w-32 bg-gray-100 rounded" />
              </div>
            ))}
          </div>
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-card p-4 shadow-card animate-pulse h-40" />
            <div className="bg-white border border-gray-200 rounded-card p-4 shadow-card animate-pulse h-48" />
          </div>
        </div>
      )}

      {/* ── Two-Column Grid ────────────────────────────────── */}
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Current Field Directives */}
          <div>
            <h3 className="text-section-title text-navy-900 mb-3">Current Field Directives</h3>
            <div className="space-y-3">
              {data.directives.map((item) => {
                const colors = urgencyColor(item.urgency);
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      if (item.documentId) {
                        navigate('/ask', { state: { question: item.title } });
                      } else {
                        navigate('/guidance');
                      }
                    }}
                    className="w-full bg-white border border-gray-200 rounded-card shadow-card hover:shadow-card-hover transition-all duration-200 p-4 text-left group focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${colors.badge}`}>
                            {item.urgency}
                          </span>
                          <span className="text-[10px] text-gray-400 font-mono">{item.code}</span>
                        </div>
                        <h4 className="text-card-title text-navy-900 mb-1 group-hover:text-primary-700 transition-colors">
                          {item.title}
                        </h4>
                        <p className="text-xs text-gray-500 mb-1">{item.authority}</p>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-gray-400 flex items-center gap-1">
                            <Clock className="h-3 w-3" /> {item.publishedAt}
                          </span>
                          <span className="text-[11px] text-gray-400 flex items-center gap-1">
                            <MapPin className="h-3 w-3" /> {item.region}
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-300 flex-shrink-0 mt-1 group-hover:text-primary-500 transition-colors" />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* District Status */}
            <div>
              <h3 className="text-section-title text-navy-900 mb-3">
                Operational Status
              </h3>
              <div className="bg-white border border-gray-200 rounded-card shadow-card p-4">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Active Mobile Units</p>
                    <div className="flex items-baseline gap-1.5">
                      <p className="text-lg font-semibold text-navy-900">{data.districtStatus.activeMobileUnits}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Total Cases</p>
                    <div className="flex items-baseline gap-1.5">
                      <p className="text-lg font-semibold text-navy-900">{data.districtStatus.totalCases}</p>
                      <TrendingUp className="h-3 w-3 text-amber-500" />
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Protocol Adoption</p>
                    <div className="flex items-baseline gap-1.5">
                      <p className="text-lg font-semibold text-navy-900">{data.districtStatus.protocolAdoption}%</p>
                      <TrendingUp className="h-3 w-3 text-green-500" />
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Current PPE Tier</p>
                    <p className="text-sm font-semibold text-navy-900">{data.districtStatus.currentPpeTier}</p>
                  </div>
                </div>

                {/* District List */}
                <div className="border-t border-gray-100 pt-3">
                  <p className="text-[11px] text-gray-400 font-medium uppercase tracking-wide mb-2">Reporting Units</p>
                  <div className="space-y-2">
                    {data.districtStatus.districts.slice(0, 3).map((district) => {
                      const dColors = districtStatusColor(district.status);
                      return (
                        <div key={district.id} className={`flex items-center justify-between px-3 py-2 rounded-lg border ${dColors.border} ${dColors.bg}`}>
                          <div className="flex items-center gap-2 min-w-0">
                            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dColors.dot}`} />
                            <div className="min-w-0">
                              <p className="text-xs font-medium text-gray-800 truncate">{district.name}</p>
                              <p className="text-[10px] text-gray-500">{district.reportingUnit}</p>
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0 ml-3">
                            <p className="text-xs font-semibold text-gray-800">{district.activeCases} cases</p>
                            <p className="text-[10px] text-gray-400">{district.lastCheckIn}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Cases Trend Chart */}
            <div>
              <h3 className="text-section-title text-navy-900 mb-3">Cases & Response Trend</h3>
              <div className="bg-white border border-gray-200 rounded-card shadow-card p-4">
                <ResponsiveContainer width="100%" height={160}>
                  <AreaChart data={data.trend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="casesGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0d9488" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="dischGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.1} />
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '12px',
                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.08)',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="cases"
                      stroke="#0d9488"
                      strokeWidth={2}
                      fill="url(#casesGradient)"
                      name="Cases"
                    />
                    <Area
                      type="monotone"
                      dataKey="discharges"
                      stroke="#22c55e"
                      strokeWidth={1.5}
                      fill="url(#dischGradient)"
                      name="Discharges"
                    />
                    <Area
                      type="monotone"
                      dataKey="tests"
                      stroke="#94a3b8"
                      strokeWidth={1}
                      fill="none"
                      strokeDasharray="4 4"
                      name="Tests"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Bottom Grid: Quick Topics + Recent Activity ─────── */}
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quick Topics */}
          <div>
            <h3 className="text-section-title text-navy-900 mb-3">Quick Topics</h3>
            <div className="space-y-2">
              {data.quickTopics.map((topic) => {
                const topicIconMap: Record<string, React.ComponentType<{ className?: string }>> = {
                  'Outbreak': AlertTriangle,
                  'Vaccination': ClipboardList,
                  'PPE & Infection Control': Shield,
                  'Emergency': Activity,
                  'Surveillance': Users,
                };
                const Icon = topicIconMap[topic.name] || FileText;
                return (
                  <button
                    key={topic.id}
                    onClick={() => handleTopicClick(topic)}
                    className="w-full flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-card hover:border-primary-200 hover:bg-primary-50/40 transition-all duration-200 group focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
                  >
                    <div className="p-1.5 rounded-md bg-gray-100 group-hover:bg-primary-100 transition-colors">
                      <Icon className="h-4 w-4 text-gray-500 group-hover:text-primary-600 transition-colors" />
                    </div>
                    <div className="flex-1 text-left min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-navy-800 group-hover:text-primary-700 transition-colors">
                          {topic.name}
                        </p>
                        <span className="inline-flex items-center justify-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-500">
                          {topic.count}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 truncate">{topic.description}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-300 group-hover:text-primary-500 transition-colors flex-shrink-0" />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Recent Activity */}
          <div>
            <h3 className="text-section-title text-navy-900 mb-3">Recent Activity</h3>
            <div className="bg-white border border-gray-200 rounded-card shadow-card divide-y divide-gray-100">
              {data.recentActivity.map((item) => {
                const Icon = getIcon(item.icon);
                return (
                  <div
                    key={item.id}
                    className={`flex items-start gap-3 px-4 py-3 ${item.documentId ? 'cursor-pointer hover:bg-gray-50 transition-colors' : ''}`}
                    onClick={() => {
                      if (item.documentId) {
                        navigate('/guidance');
                      }
                    }}
                  >
                    <div className="p-1 rounded bg-gray-50 mt-0.5">
                      <Icon className="h-3.5 w-3.5 text-gray-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 leading-snug font-medium">{item.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{item.action}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <p className="text-[11px] text-gray-400">{item.timestamp}</p>
                        <span className="text-[11px] text-gray-300">•</span>
                        <p className="text-[11px] text-gray-400">{item.actor}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
