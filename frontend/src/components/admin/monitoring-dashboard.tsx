/**
 * Comprehensive monitoring dashboard for system health and performance tracking.
 * Displays real-time metrics, health status, and performance alerts.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { errorReportingService } from '@/lib/error-reporting';

interface SystemMetrics {
  timestamp: string;
  uptime_seconds: number;
  cpu: {
    percent: number;
    count: number;
    frequency_mhz?: number;
  };
  memory: {
    total_gb: number;
    available_gb: number;
    used_gb: number;
    percent: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  };
  process: {
    memory_mb: number;
    cpu_percent: number;
    threads: number;
    open_files: number;
    connections: number;
  };
}

interface ApplicationMetrics {
  timestamp: string;
  requests: {
    total: number;
    errors: number;
    error_rate_percent: number;
  };
  performance: {
    slow_endpoints: Array<{
      path: string;
      count: number;
      avg_duration_ms: number;
      error_count: number;
      error_rate: number;
    }>;
    total_endpoints: number;
  };
}

interface DatabaseMetrics {
  timestamp: string;
  connectivity: {
    status: string;
    response_time_ms: number;
  };
  tables: {
    jobs: number;
    payments: number;
    events: number;
  };
  recent_activity: {
    jobs_last_24h: number;
    events_last_24h: number;
  };
}

interface StorageMetrics {
  timestamp: string;
  status: string;
  path: string;
  files: {
    count: number;
    directories: number;
    total_size_gb: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent_used: number;
  };
}

interface RedisMetrics {
  timestamp: string;
  connectivity: {
    status: string;
    response_time_ms: number;
  };
  redis: {
    version: string;
    uptime_seconds: number;
    connected_clients: number;
    used_memory_mb: number;
    total_commands_processed: number;
  };
  rq: {
    queue_size: number;
  };
}

interface HealthStatus {
  status: string;
  timestamp: string;
  uptime_seconds: number;
  health_checks: {
    system: string;
    database: string;
    storage: string;
    redis: string;
  };
  components: {
    system: SystemMetrics;
    application: ApplicationMetrics;
    database: DatabaseMetrics;
    storage: StorageMetrics;
    redis: RedisMetrics;
  };
}

interface PerformanceAlert {
  type: string;
  severity: 'warning' | 'critical' | 'error';
  message: string;
  timestamp: string;
}

const MonitoringDashboard: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds

  // Fetch health status
  const fetchHealthStatus = async () => {
    try {
      const response = await fetch('/api/v1/monitoring/health');
      if (response.ok) {
        const data = await response.json();
        setHealthStatus(data);
        setError(null);
      } else {
        throw new Error(`Health check failed: ${response.status}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health status');
    }
  };

  // Fetch performance alerts
  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/v1/monitoring/alerts');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (err) {
      console.warn('Failed to fetch alerts:', err);
    }
  };

  // Fetch all data
  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchHealthStatus(), fetchAlerts()]);
    setLoading(false);
  };

  // Auto-refresh effect
  useEffect(() => {
    fetchData();

    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // Format uptime
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Get severity color
  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100 border-red-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'error':
        return 'text-red-600 bg-red-100 border-red-200';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  if (loading && !healthStatus) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
          <p className="text-gray-600">Real-time system health and performance metrics</p>
        </div>
        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm">Auto-refresh</span>
          </label>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="text-sm border rounded px-2 py-1"
            disabled={!autoRefresh}
          >
            <option value={10}>10s</option>
            <option value={30}>30s</option>
            <option value={60}>1m</option>
            <option value={300}>5m</option>
          </select>
          <button
            onClick={fetchData}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {healthStatus && (
        <>
          {/* Overall Health Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">System Health</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(healthStatus.status)}`}>
                  {healthStatus.status}
                </div>
                <p className="text-sm text-gray-600 mt-1">Overall Status</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {formatUptime(healthStatus.uptime_seconds)}
                </div>
                <p className="text-sm text-gray-600">Uptime</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {new Date(healthStatus.timestamp).toLocaleTimeString()}
                </div>
                <p className="text-sm text-gray-600">Last Updated</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {alerts.length}
                </div>
                <p className="text-sm text-gray-600">Active Alerts</p>
              </div>
            </div>
          </div>

          {/* Component Health */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Component Health</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(healthStatus.health_checks).map(([component, status]) => (
                <div key={component} className="text-center">
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
                    {status}
                  </div>
                  <p className="text-sm text-gray-600 mt-1 capitalize">{component}</p>
                </div>
              ))}
            </div>
          </div>

          {/* System Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CPU and Memory */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">CPU & Memory</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm">
                    <span>CPU Usage</span>
                    <span>{healthStatus.components.system.cpu.percent}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${healthStatus.components.system.cpu.percent}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Memory Usage</span>
                    <span>{healthStatus.components.system.memory.percent}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${healthStatus.components.system.memory.percent}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {healthStatus.components.system.memory.used_gb}GB / {healthStatus.components.system.memory.total_gb}GB
                  </p>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Disk Usage</span>
                    <span>{healthStatus.components.system.disk.percent}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-600 h-2 rounded-full"
                      style={{ width: `${healthStatus.components.system.disk.percent}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {healthStatus.components.system.disk.used_gb}GB / {healthStatus.components.system.disk.total_gb}GB
                  </p>
                </div>
              </div>
            </div>

            {/* Application Metrics */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Application</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {healthStatus.components.application.requests.total.toLocaleString()}
                    </div>
                    <p className="text-sm text-gray-600">Total Requests</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {healthStatus.components.application.requests.errors.toLocaleString()}
                    </div>
                    <p className="text-sm text-gray-600">Errors</p>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Error Rate</span>
                    <span>{healthStatus.components.application.requests.error_rate_percent}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-600 h-2 rounded-full"
                      style={{ width: `${healthStatus.components.application.requests.error_rate_percent}%` }}
                    ></div>
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {healthStatus.components.application.performance.total_endpoints}
                  </div>
                  <p className="text-sm text-gray-600">Active Endpoints</p>
                </div>
              </div>
            </div>
          </div>

          {/* Database and Storage */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Database</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm">Status</span>
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(healthStatus.components.database.connectivity.status)}`}>
                    {healthStatus.components.database.connectivity.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Response Time</span>
                  <span className="text-sm">{healthStatus.components.database.connectivity.response_time_ms}ms</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-900">
                      {healthStatus.components.database.tables.jobs.toLocaleString()}
                    </div>
                    <p className="text-sm text-gray-600">Jobs</p>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-900">
                      {healthStatus.components.database.tables.events.toLocaleString()}
                    </div>
                    <p className="text-sm text-gray-600">Events</p>
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-blue-600">
                    {healthStatus.components.database.recent_activity.jobs_last_24h}
                  </div>
                  <p className="text-sm text-gray-600">Jobs (24h)</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Storage</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm">Status</span>
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(healthStatus.components.storage.status)}`}>
                    {healthStatus.components.storage.status}
                  </span>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-gray-900">
                    {healthStatus.components.storage.files.count.toLocaleString()}
                  </div>
                  <p className="text-sm text-gray-600">Files</p>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-gray-900">
                    {healthStatus.components.storage.files.total_size_gb}GB
                  </div>
                  <p className="text-sm text-gray-600">Total Size</p>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Storage Usage</span>
                    <span>{healthStatus.components.storage.disk.percent_used}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${healthStatus.components.storage.disk.percent_used}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Performance Alerts */}
          {alerts.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Performance Alerts</h3>
              <div className="space-y-3">
                {alerts.map((alert, index) => (
                  <div
                    key={index}
                    className={`p-4 border rounded-lg ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium">{alert.message}</div>
                        <div className="text-sm opacity-75 mt-1">
                          {new Date(alert.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Slow Endpoints */}
          {healthStatus.components.application.performance.slow_endpoints.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Slow Endpoints</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Endpoint</th>
                      <th className="text-right py-2">Requests</th>
                      <th className="text-right py-2">Avg Duration</th>
                      <th className="text-right py-2">Error Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {healthStatus.components.application.performance.slow_endpoints.slice(0, 5).map((endpoint, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2 font-mono text-sm">{endpoint.path}</td>
                        <td className="py-2 text-right">{endpoint.count}</td>
                        <td className="py-2 text-right">
                          <span className={endpoint.avg_duration_ms > 1000 ? 'text-red-600 font-medium' : ''}>
                            {endpoint.avg_duration_ms}ms
                          </span>
                        </td>
                        <td className="py-2 text-right">
                          <span className={endpoint.error_rate > 5 ? 'text-red-600 font-medium' : ''}>
                            {endpoint.error_rate}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MonitoringDashboard;
