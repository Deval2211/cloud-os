/**
 * Session management component
 */
'use client';

import { useState } from 'react';
import { useSessions, useSessionMetrics } from '@/hooks/useSessions';

interface SessionsProps {
  workspaceId: string;
}

export function SessionsPanel({ workspaceId }: SessionsProps) {
  const {
    sessions,
    currentSession,
    isLoading,
    error,
    startSession,
    stopSession,
    setCurrentSession,
  } = useSessions(workspaceId);

  const { metrics, isLive } = useSessionMetrics(currentSession?.id || null);
  const [isStarting, setIsStarting] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState('local_docker');
  const [selectedGPU, setSelectedGPU] = useState('');

  const handleStartSession = async () => {
    try {
      setIsStarting(true);
      const session = await startSession({
        provider: selectedProvider,
        gpu_type: selectedGPU || undefined,
        memory_gb: 16,
        timeout_hours: 1,
      });
      setCurrentSession(session);
    } catch (err) {
      console.error('Failed to start session:', err);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopSession = async (sessionId: string) => {
    try {
      await stopSession(sessionId);
    } catch (err) {
      console.error('Failed to stop session:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-900 text-green-100';
      case 'pending':
        return 'bg-yellow-900 text-yellow-100';
      case 'stopped':
        return 'bg-gray-700 text-gray-200';
      case 'error':
        return 'bg-red-900 text-red-100';
      default:
        return 'bg-gray-700 text-gray-200';
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 border-l border-gray-800">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-lg font-semibold mb-4">GPU Sessions</h2>

        {/* Start Session Form */}
        <div className="space-y-3">
          <div>
            <label className="text-sm text-gray-400 block mb-1">Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              disabled={isStarting}
              className="w-full bg-gray-900 text-gray-100 border border-gray-700 rounded px-3 py-2 text-sm hover:border-gray-600 focus:border-sky-500 outline-none disabled:opacity-50"
            >
              <option value="local_docker">Local Docker</option>
              <option value="runpod">RunPod</option>
              <option value="vast_ai">Vast.ai</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-400 block mb-1">GPU Type (Optional)</label>
            <input
              type="text"
              value={selectedGPU}
              onChange={(e) => setSelectedGPU(e.target.value)}
              placeholder="e.g., RTX 4090"
              disabled={isStarting}
              className="w-full bg-gray-900 text-gray-100 border border-gray-700 rounded px-3 py-2 text-sm hover:border-gray-600 focus:border-sky-500 outline-none placeholder-gray-600 disabled:opacity-50"
            />
          </div>

          <button
            onClick={handleStartSession}
            disabled={isStarting || isLoading}
            className="w-full bg-sky-600 hover:bg-sky-700 disabled:bg-gray-700 text-white py-2 px-4 rounded font-medium text-sm transition-colors"
          >
            {isStarting ? 'Starting...' : 'Start Session'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-900 text-red-100 text-sm border-l-4 border-red-600">
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-400">Loading sessions...</div>
        </div>
      )}

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">No sessions yet</div>
        ) : (
          <div className="p-4 space-y-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => setCurrentSession(session)}
                className={`p-3 rounded border cursor-pointer transition-colors ${
                  currentSession?.id === session.id
                    ? 'border-sky-500 bg-sky-950 bg-opacity-20'
                    : 'border-gray-700 hover:border-gray-600 hover:bg-gray-900 hover:bg-opacity-50'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{session.provider}</div>
                    <div className="text-xs text-gray-500 font-mono">{session.id.slice(0, 12)}...</div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded font-medium ${getStatusColor(session.status)}`}>
                    {session.status}
                  </span>
                </div>

                {session.config?.gpu_type && (
                  <div className="text-xs text-gray-400 mb-2">GPU: {session.config.gpu_type}</div>
                )}

                {currentSession?.id === session.id && session.status === 'running' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStopSession(session.id);
                    }}
                    className="mt-2 w-full bg-red-900 hover:bg-red-800 text-red-100 py-1 px-2 rounded text-xs font-medium transition-colors"
                  >
                    Stop Session
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metrics Footer */}
      {currentSession && metrics && isLive && (
        <div className="p-4 border-t border-gray-800 bg-gray-900 bg-opacity-50">
          <div className="text-xs text-gray-400 mb-2 font-semibold">Live Metrics</div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-500">GPU Usage</span>
              <span className="text-gray-300">{metrics.gpu_usage?.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Memory</span>
              <span className="text-gray-300">{metrics.gpu_memory_used} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Temperature</span>
              <span className="text-gray-300">{metrics.gpu_temperature}°C</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
