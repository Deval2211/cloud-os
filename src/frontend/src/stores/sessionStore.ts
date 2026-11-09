import { create } from 'zustand';

export interface SessionMetrics {
  gpuUsage: number;
  memoryUsage: number;
  cpuUsage: number;
  temperature: number;
  networkIn: number;
  networkOut: number;
}

export interface WorkspaceSession {
  id: string;
  workspaceId: string;
  provider: string;
  status: 'pending' | 'running' | 'stopped' | 'error';
  gpuType: string;
  gpuCount: number;
  hourlyRate: number;
  currentCost: number;
  startedAt: string;
  metrics: SessionMetrics;
}

export interface SessionState {
  currentSession: WorkspaceSession | null;
  activeSessions: WorkspaceSession[];
  setCurrentSession: (session: WorkspaceSession | null) => void;
  addActiveSession: (session: WorkspaceSession) => void;
  removeActiveSession: (id: string) => void;
  updateSessionMetrics: (id: string, metrics: SessionMetrics) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  currentSession: null,
  activeSessions: [],

  setCurrentSession: (session: WorkspaceSession | null) =>
    set({ currentSession: session }),

  addActiveSession: (session: WorkspaceSession) =>
    set((state) => ({
      activeSessions: [...state.activeSessions, session],
    })),

  removeActiveSession: (id: string) =>
    set((state) => ({
      activeSessions: state.activeSessions.filter((s) => s.id !== id),
    })),

  updateSessionMetrics: (id: string, metrics: SessionMetrics) =>
    set((state) => ({
      currentSession:
        state.currentSession?.id === id
          ? { ...state.currentSession, metrics }
          : state.currentSession,
      activeSessions: state.activeSessions.map((s) =>
        s.id === id ? { ...s, metrics } : s
      ),
    })),
}));
