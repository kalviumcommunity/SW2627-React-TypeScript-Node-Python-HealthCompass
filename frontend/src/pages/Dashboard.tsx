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
  Search,
  TrendingUp,
  ChevronRight,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getStats } from '../api/client';
import type { Stats } from '../api/client';
import {
  currentUser,
  activeDirective,
  fieldDirectives,
  districtStatus,
  quickTopics,
  suggestedQuestions,
  casesTrend,
  recentActivity,
} from '../data/dashboard';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

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
};

function getIcon(name: string) {
  return iconMap[name] || FileText;
}

// ─── Dashboard ───────────────────────────────────────────────────

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [now] = useState(() => new Date());

  const loadStats = useCallback(async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handleQuickAsk = () => {
    if (query.trim()) {
      navigate('/ask', { state: { question: query } });
    }
  };

  const handleSuggestedQuery = (question: string) => {
    navigate('/ask', { state: { question } });
  };

  const handleTopicClick = (topic: { title: string; href: string }) => {
    navigate(topic.href, { state: { question: topic.title } });
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

  // ─── Metric Cards Data ──────────────────────────────────────

  const metricCards = stats
    ? [
        {
          id: 'alerts',
          icon: Activity,
          value: stats.active_alerts,
          label: 'Active Alerts',
          subtitle: stats.active_alerts_subtitle || '',
          href: '/alerts',
          accentColor: 'text-red-600',
          bgColor: 'bg-red-50',
        },
        {
          id: 'guidance',
          icon: BookOpen,
          value: stats.new_guidance,
          label: 'New Guidance',
          subtitle: stats.new_guidance_subtitle || '',
          href: '/guidance',
          accentColor: 'text-primary-600',
          bgColor: 'bg-primary-50',
        },
        {
          id: 'updates',
          icon: FileText,
          value: stats.policy_updates,
          label: 'Policy Updates',
          subtitle: stats.policy_updates_subtitle || '',
          href: '/updates',
          accentColor: 'text-amber-600',
          bgColor: 'bg-amber-50',
        },
        {
          id: 'saved',
          icon: Bookmark,
          value: stats.saved_guidance,
          label: 'Saved Guidance',
          subtitle: stats.saved_guidance_subtitle || '',
          href: '/saved',
          accentColor: 'text-indigo-600',
          bgColor: 'bg-indigo-50',
        },
      ]
    : [];

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
            {stats && stats.active_alerts > 0 && (
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

      {/* ── Active Directive ───────────────────────────────── */}
      <div className="bg-white border border-gray-200 rounded-card shadow-card mb-6 border-l-4 border-l-primary-600 overflow-hidden">
        <div className="p-4 flex items-start gap-3">
          <div className="w-9 h-9 bg-primary-50 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
            <AlertTriangle className="h-4.5 w-4.5 text-primary-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-green-100 text-green-700 uppercase tracking-wide">
                {activeDirective.status}
              </span>
              <span className="text-xs text-gray-400">{activeDirective.region}</span>
            </div>
            <h3 className="text-sm font-semibold text-navy-900 mb-1">{activeDirective.title}</h3>
            <p className="text-xs text-gray-600 leading-relaxed mb-2">{activeDirective.description}</p>
            <div className="flex items-center gap-3">
              {activeDirective.actions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => navigate(action.href)}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 transition-colors"
                >
                  {action.label}
                  <ArrowRight className="h-3 w-3" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Two-Column Grid ────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Current Field Directives */}
        <div>
          <h3 className="text-section-title text-navy-900 mb-3">Current Field Directives</h3>
          <div className="space-y-3">
            {fieldDirectives.map((item) => (
              <button
                key={item.id}
                onClick={() => navigate('/guidance')}
                className="w-full bg-white border border-gray-200 rounded-card shadow-card hover:shadow-card-hover transition-all duration-200 p-4 text-left group focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-green-100 text-green-700 uppercase tracking-wide">
                        {item.status}
                      </span>
                    </div>
                    <h4 className="text-card-title text-navy-900 mb-1 group-hover:text-primary-700 transition-colors">
                      {item.title}
                    </h4>
                    <p className="text-xs text-gray-500 mb-1">{item.authority}</p>
                    <p className="text-[11px] text-gray-400">Effective {item.effectiveDate}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-300 flex-shrink-0 mt-1 group-hover:text-primary-500 transition-colors" />
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* District Status */}
          <div>
            <h3 className="text-section-title text-navy-900 mb-3">
              {districtStatus.name} Status
            </h3>
            <div className="bg-white border border-gray-200 rounded-card shadow-card p-4">
              <div className="grid grid-cols-2 gap-4">
                {districtStatus.metrics.map((metric) => (
                  <div key={metric.label}>
                    <p className="text-xs text-gray-500 mb-1">{metric.label}</p>
                    <div className="flex items-baseline gap-1.5">
                      <p className="text-lg font-semibold text-navy-900">{metric.value}</p>
                      {metric.trend === 'up' && (
                        <TrendingUp className="h-3 w-3 text-amber-500" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cases Trend Chart */}
          <div>
            <h3 className="text-section-title text-navy-900 mb-3">Cases & Response Trend</h3>
            <div className="bg-white border border-gray-200 rounded-card shadow-card p-4">
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={casesTrend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="casesGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0d9488" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
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
                    dataKey="responses"
                    stroke="#94a3b8"
                    strokeWidth={1.5}
                    fill="none"
                    strokeDasharray="4 4"
                    name="Responses"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Grid: Quick Topics + Recent Activity ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Topics */}
        <div>
          <h3 className="text-section-title text-navy-900 mb-3">Quick Topics</h3>
          <div className="space-y-2">
            {quickTopics.map((topic) => {
              const Icon = getIcon(topic.icon);
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
                    <p className="text-sm font-medium text-navy-800 group-hover:text-primary-700 transition-colors">
                      {topic.title}
                    </p>
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
            {recentActivity.map((item) => {
              const Icon = getIcon(item.icon);
              return (
                <div key={item.id} className="flex items-start gap-3 px-4 py-3">
                  <div className="p-1 rounded bg-gray-50 mt-0.5">
                    <Icon className="h-3.5 w-3.5 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 leading-snug">{item.description}</p>
                    <p className="text-[11px] text-gray-400 mt-0.5">{item.timestamp}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
