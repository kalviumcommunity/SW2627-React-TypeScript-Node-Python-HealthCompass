import { useState, useEffect } from 'react';
import { ArrowRight, AlertTriangle, FileText, BookOpen, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getStats } from '../api/client';
import type { Stats } from '../api/client';

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAsk = () => {
    navigate('/ask');
  };

  return (
    <div>
      {/* Greeting */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Good morning, Sarah
        </h1>
        <p className="text-gray-600">
          Stay informed. Make better decisions in the field.
        </p>
      </div>

      {/* Quick Stats */}
      {!loading && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <AlertTriangle className="h-6 w-6 text-orange-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.active_alerts}</span>
            </div>
            <p className="text-sm text-gray-600">Active Alerts</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <BookOpen className="h-6 w-6 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.new_guidance}</span>
            </div>
            <p className="text-sm text-gray-600">New Guidance</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <FileText className="h-6 w-6 text-purple-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.policy_updates}</span>
            </div>
            <p className="text-sm text-gray-600">Policy Updates</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <MessageSquare className="h-6 w-6 text-green-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.saved_guidance}</span>
            </div>
            <p className="text-sm text-gray-600">Saved Guidance</p>
          </div>
        </div>
      )}

      {/* Quick Ask */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-sm p-8 mb-8 text-white">
        <h2 className="text-2xl font-bold mb-2">Ask HealthCompass</h2>
        <p className="text-blue-100 mb-6">
          Get evidence-based guidance from the HealthCompass knowledge base
        </p>
        <button
          onClick={handleQuickAsk}
          className="flex items-center gap-2 px-6 py-3 bg-white text-blue-700 rounded-lg font-medium hover:bg-blue-50 transition-colors"
        >
          <MessageSquare className="h-5 w-5" />
          Ask HealthCompass
          <ArrowRight className="h-5 w-5" />
        </button>
      </div>

      {/* Recent Guidance */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Guidance</h2>
          <button
            onClick={() => navigate('/guidance')}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            View all →
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer">
            <h3 className="font-semibold text-gray-900 mb-2">Vaccination Priority Groups</h3>
            <p className="text-sm text-gray-600 mb-3">
              Guidance on priority groups for vaccination during public health emergencies
            </p>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Vaccination</span>
              <span>Updated Sep 15</span>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer">
            <h3 className="font-semibold text-gray-900 mb-2">Fever Management in Children</h3>
            <p className="text-sm text-gray-600 mb-3">
              Protocol for managing high fever in pediatric patients
            </p>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Child Health</span>
              <span>Updated Sep 10</span>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer">
            <h3 className="font-semibold text-gray-900 mb-2">Emergency Response Protocol</h3>
            <p className="text-sm text-gray-600 mb-3">
              Standard operating procedures for emergency health situations
            </p>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Emergency Response</span>
              <span>Updated Sep 8</span>
            </div>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Active Alerts</h2>
          <button
            onClick={() => navigate('/alerts')}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            View all →
          </button>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="h-6 w-6 text-orange-600" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-semibold text-orange-900 bg-orange-100 px-2 py-1 rounded">
                  Critical
                </span>
                <span className="text-sm text-gray-600">Disease Outbreak</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-1">
                Increased respiratory illness cases in District A
              </h3>
              <p className="text-sm text-gray-600">
                Reported Sep 28 · District A · Monitoring
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
