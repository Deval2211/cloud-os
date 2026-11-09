/**
 * Hooks for session management
 */
import { useCallback, useEffect, useState } from 'react';
import { useWebSocketStore } from '@/stores/websocketStore';
import { EventType } from '@/api/websocket';
import apiClient from '@/api/client';

export interface Session {
  id: string;
  workspace_id: string;
  provider: string;
  status: 'pending' | 'running' | 'stopped' | 'error';
  created_at: string;
  updated_at: string;
  config: Record<string, any>;
}

export interface UseSessionsReturn {
  sessions: Session[];
  currentSession: Session | null;
  isLoading: boolean;
  error: string | null;
  startSession: (config: {
    provider?: string;
    gpu_type?: string;
    memory_gb?: number;
    timeout_hours?: number;
  }) => Promise<Session>;
  stopSession: (sessionId: string) => Promise<void>;
  loadSessions: () => Promise<void>;
  setCurrentSession: (session: Session | null) => void;
}

/**
 * Hook for managing GPU sessions
 */
export const useSessions = (workspaceId: string): UseSessionsReturn => {
  const { client, isConnected } = useWebSocketStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load sessions from server
  const loadSessions = useCallback(async () => {
    if (!workspaceId) return;

    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.getSessions(workspaceId);
      setSessions(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load sessions';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  // Start a new session
  const startSession = useCallback(
    async (config) => {
      if (!workspaceId) throw new Error('No workspace selected');

      try {
        setIsLoading(true);
        setError(null);
        const session = await apiClient.startSession(workspaceId, {
          workspace_id: workspaceId,
          provider: config.provider || 'local_docker',
          gpu_type: config.gpu_type,
          memory_gb: config.memory_gb || 16,
          timeout_hours: config.timeout_hours || 1,
        });
        setSessions((prev) => [...prev, session]);
        setCurrentSession(session);
        return session;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to start session';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [workspaceId]
  );

  // Stop a session
  const stopSession = useCallback(
    async (sessionId: string) => {
      try {
        setError(null);
        await apiClient.stopSession(workspaceId, sessionId);

        // Update local state
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId ? { ...s, status: 'stopped' as const } : s
          )
        );

        if (currentSession?.id === sessionId) {
          setCurrentSession(null);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to stop session';
        setError(message);
        throw err;
      }
    },
    [workspaceId, currentSession]
  );

  // Listen to WebSocket events for real-time updates
  useEffect(() => {
    if (!client || !isConnected) return;

    // Handle session started
    const unsubscribeStarted = client.on(EventType.SESSION_STARTED, (event) => {
      if (event.workspace_id !== workspaceId) return;

      const newSession: Session = {
        id: event.data.session_id,
        workspace_id: workspaceId,
        provider: event.data.provider,
        status: 'running',
        created_at: event.timestamp,
        updated_at: event.timestamp,
        config: {
          gpu_type: event.data.gpu_type,
        },
      };

      setSessions((prev) => [...prev, newSession]);
      if (!currentSession) {
        setCurrentSession(newSession);
      }
    });

    // Handle session stopped
    const unsubscribeStopped = client.on(EventType.SESSION_STOPPED, (event) => {
      if (event.workspace_id !== workspaceId) return;

      setSessions((prev) =>
        prev.map((s) =>
          s.id === event.data.session_id ? { ...s, status: 'stopped' } : s
        )
      );

      if (currentSession?.id === event.data.session_id) {
        setCurrentSession(null);
      }
    });

    // Handle session error
    const unsubscribeError = client.on(EventType.SESSION_ERROR, (event) => {
      if (event.workspace_id !== workspaceId) return;

      setError(event.data.error || 'Session error occurred');

      setSessions((prev) =>
        prev.map((s) =>
          s.id === event.data.session_id ? { ...s, status: 'error' } : s
        )
      );
    });

    // Handle session status update
    const unsubscribeStatus = client.on(EventType.SESSION_STATUS_UPDATE, (event) => {
      if (event.workspace_id !== workspaceId) return;

      setSessions((prev) =>
        prev.map((s) =>
          s.id === event.data.session_id
            ? { ...s, status: event.data.status, updated_at: event.timestamp }
            : s
        )
      );
    });

    return () => {
      unsubscribeStarted();
      unsubscribeStopped();
      unsubscribeError();
      unsubscribeStatus();
    };
  }, [client, isConnected, workspaceId, currentSession]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return {
    sessions,
    currentSession,
    isLoading,
    error,
    startSession,
    stopSession,
    loadSessions,
    setCurrentSession,
  };
};

/**
 * Hook for monitoring session metrics
 */
export const useSessionMetrics = (sessionId: string | null) => {
  const { client, isConnected } = useWebSocketStore();
  const [metrics, setMetrics] = useState<any>(null);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    if (!client || !isConnected || !sessionId) {
      setIsLive(false);
      return;
    }

    setIsLive(true);

    // Handle metrics updates
    const unsubscribe = client.on(EventType.METRICS_UPDATE, (event) => {
      if (event.session_id !== sessionId) return;

      setMetrics({
        timestamp: event.timestamp,
        ...event.data.metrics,
      });
    });

    return () => {
      unsubscribe();
      setIsLive(false);
    };
  }, [client, isConnected, sessionId]);

  return { metrics, isLive };
};

/**
 * Hook for terminal I/O
 */
export const useTerminal = (sessionId: string | null) => {
  const { client, isConnected } = useWebSocketStore();
  const [output, setOutput] = useState<string>('');
  const [history, setHistory] = useState<string[]>([]);

  const sendCommand = useCallback(
    (command: string) => {
      if (!client || !isConnected || !sessionId) return;

      client.sendEvent({
        type: EventType.TERMINAL_INPUT,
        data: { command, session_id: sessionId },
        timestamp: new Date().toISOString(),
      });

      setHistory((prev) => [...prev, command]);
    },
    [client, isConnected, sessionId]
  );

  useEffect(() => {
    if (!client || !isConnected || !sessionId) return;

    const unsubscribe = client.on(EventType.TERMINAL_OUTPUT, (event) => {
      if (event.session_id !== sessionId) return;

      setOutput((prev) => prev + event.data.output);
    });

    return unsubscribe;
  }, [client, isConnected, sessionId]);

  return {
    output,
    history,
    sendCommand,
    clearOutput: () => setOutput(''),
  };
};
