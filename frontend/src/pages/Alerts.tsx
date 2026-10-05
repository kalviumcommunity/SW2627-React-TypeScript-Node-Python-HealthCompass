import { useState, useEffect } from 'react';
import { AlertTriangle, Shield, AlertCircle, Info, MapPin, Calendar } from 'lucide-react';
import { getAlerts, ApiError } from '../api/client';
import type { AlertItem } from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

function Alerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const data = await getAlerts();
      setAlerts(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load alerts');
      }
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return AlertTriangle;
      case 'high':
        return Shield;
      case 'medium':
        return AlertCircle;
      default:
        return Info;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'text-red-600 bg-red-50';
      case 'high':
        return 'text-orange-600 bg-orange-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-blue-600 bg-blue-50';
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'error';
      case 'monitoring':
        return 'warning';
      default:
        return 'info';
    }
  };

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Alert Center</h1>
        <p className="text-sm text-gray-500">Monitor important public health alerts and notifications.</p>
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
          <p className="text-sm text-gray-500">Loading alerts...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && alerts.length === 0 && (
        <div className="text-center py-12">
          <p className="text-sm text-gray-500">No active alerts</p>
        </div>
      )}

      {/* Alerts List */}
      {!loading && alerts.length > 0 && (
        <div className="space-y-4">
          {alerts.map((alert) => {
            const SeverityIcon = getSeverityIcon(alert.severity);
            return (
              <Card key={alert.id} className="p-5 border-l-4 border-l-gray-200 hover:border-l-red-400 transition-colors">
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${getSeverityColor(alert.severity)}`}>
                    <SeverityIcon className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs font-semibold px-2 py-1 rounded ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <Badge variant={getStatusVariant(alert.status)}>
                        {alert.status}
                      </Badge>
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-1">{alert.topic}</h3>
                    <p className="text-sm text-gray-600 mb-3">{alert.description}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      {alert.location && (
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          <span>{alert.location}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{alert.date}</span>
                      </div>
                    </div>
                  </div>
                  <button className="text-xs text-teal-600 hover:text-teal-700 font-medium">
                    View Details →
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Alerts;
