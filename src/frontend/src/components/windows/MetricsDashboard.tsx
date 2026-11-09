/**
 * Metrics dashboard component for real-time monitoring
 */
'use client';

import { useEffect, useState } from 'react';
import { useSessionMetrics } from '@/hooks/useSessions';

interface MetricsDashboardProps {
  sessionId: string | null;
  onClose?: () => void;
}

interface MetricsData {
  timestamp: string;
  gpu_usage: number;
  gpu_memory_used: number;
  gpu_memory_total: number;
  gpu_temperature: number;
  cpu_usage: number;
  system_memory: number;
  disk_usage: number;
}

export function MetricsDashboard({ sessionId, onClose }: MetricsDashboardProps) {
  const { metrics, isLive } = useSessionMetrics(sessionId);
  const [metricsHistory, setMetricsHistory] = useState<MetricsData[]>([]);
  const [maxMetrics, setMaxMetrics] = useState({
    gpu_usage: 0,
    cpu_usage: 0,
    gpu_temperature: 0,
  });

  useEffect(() => {
    if (!metrics) return;

    const metricsData = metrics as MetricsData;
    setMetricsHistory((prev) => {
      const updated = [...prev, metricsData];
      // Keep last 100 data points
      return updated.slice(-100);
    });

    // Track max values
    setMaxMetrics((prev) => ({
      gpu_usage: Math.max(prev.gpu_usage, metricsData.gpu_usage || 0),
      cpu_usage: Math.max(prev.cpu_usage, metricsData.cpu_usage || 0),
      gpu_temperature: Math.max(prev.gpu_temperature, metricsData.gpu_temperature || 0),
    }));
  }, [metrics]);

  const currentMetrics = metrics as MetricsData | null;
  const avgGpuUsage =
    metricsHistory.length > 0
      ? (metricsHistory.reduce((sum, m) => sum + (m.gpu_usage || 0), 0) / metricsHistory.length).toFixed(1)
      : '0.0';

  const MetricCard = ({ label, value, unit, max, color }: any) => {
    const percentage = max > 0 ? (value / max) * 100 : 0;
    const barColor =
      percentage > 80 ? 'bg-red-600' : percentage > 50 ? 'bg-yellow-600' : 'bg-green-600';

    return (
      <div className="bg-gray-900 rounded p-3 border border-gray-800">
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-xs text-gray-400">{label}</span>
          <span className={`font-semibold ${color}`}>
            {value.toFixed(1)}{unit}
          </span>
        </div>
        <div className="w-full bg-gray-800 rounded h-2 overflow-hidden">
          <div
            className={`h-full ${barColor} transition-all`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          ></div>
        </div>
        {max && <div className="text-xs text-gray-500 mt-1">Max: {max.toFixed(1)}{unit}</div>}
      </div>
    );
  };

  if (!sessionId) {
    return (
      <div className="flex flex-col h-full bg-gray-950 text-gray-100 border border-gray-700 rounded">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h3 className="font-semibold">Metrics</h3>
          {onClose && (
            <button onClick={onClose} className="text-gray-400 hover:text-gray-200">
              ✕
            </button>
          )}
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-500">Start a session to view metrics</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 border border-gray-700 rounded">
      {/* Header */}
      <div className="p-3 border-b border-gray-700 flex justify-between items-center bg-gray-900">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500' : 'bg-gray-500'}`}></div>
          <h3 className="font-semibold">Metrics</h3>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 text-lg leading-none"
          >
            ✕
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {!isLive ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Waiting for metrics...
          </div>
        ) : currentMetrics ? (
          <>
            {/* GPU Section */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase">GPU</h4>
              <div className="space-y-2">
                <MetricCard
                  label="Usage"
                  value={currentMetrics.gpu_usage}
                  unit="%"
                  max={100}
                  color="text-blue-400"
                />
                <MetricCard
                  label="Memory"
                  value={currentMetrics.gpu_memory_used}
                  unit=" MB"
                  max={currentMetrics.gpu_memory_total}
                  color="text-purple-400"
                />
                <MetricCard
                  label="Temperature"
                  value={currentMetrics.gpu_temperature}
                  unit="°C"
                  max={maxMetrics.gpu_temperature}
                  color="text-red-400"
                />
              </div>
            </div>

            {/* CPU Section */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase">CPU</h4>
              <div className="space-y-2">
                <MetricCard
                  label="Usage"
                  value={currentMetrics.cpu_usage}
                  unit="%"
                  max={100}
                  color="text-green-400"
                />
                <MetricCard
                  label="Memory"
                  value={currentMetrics.system_memory}
                  unit=" MB"
                  max={16384}
                  color="text-cyan-400"
                />
              </div>
            </div>

            {/* Storage Section */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase">Storage</h4>
              <MetricCard
                label="Disk Usage"
                value={currentMetrics.disk_usage}
                unit="%"
                max={100}
                color="text-yellow-400"
              />
            </div>

            {/* Stats */}
            <div className="pt-2 border-t border-gray-800">
              <div className="text-xs text-gray-500 space-y-1">
                <div className="flex justify-between">
                  <span>Avg GPU Usage:</span>
                  <span>{avgGpuUsage}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Data Points:</span>
                  <span>{metricsHistory.length}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last Update:</span>
                  <span>{new Date(currentMetrics.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
