/**
 * WebSocket state management
 */
import { create } from 'zustand';
import { WebSocketClient, EventType } from '../api/websocket';

export interface WebSocketStoreState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  workspaceId: string | null;
  activeUsers: string[];
  client: WebSocketClient | null;

  // Actions
  connect: (workspaceId: string, token: string) => Promise<void>;
  disconnect: () => void;
  setError: (error: string | null) => void;
  setActiveUsers: (users: string[]) => void;
  addUser: (userId: string) => void;
  removeUser: (userId: string) => void;
}

export const useWebSocketStore = create<WebSocketStoreState>((set, get) => ({
  isConnected: false,
  isConnecting: false,
  error: null,
  workspaceId: null,
  activeUsers: [],
  client: null,

  connect: async (workspaceId: string, token: string) => {
    try {
      set({ isConnecting: true, error: null });

      // Get API URL from environment or default
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const client = new WebSocketClient(apiUrl, token, workspaceId);

      // Set up event listeners
      client.on(EventType.CONNECTION_ESTABLISHED, (event) => {
        console.log('Connection established:', event.data);
        if (event.data.active_users) {
          set({ activeUsers: event.data.active_users });
        }
      });

      client.on(EventType.USER_JOINED, (event) => {
        const userId = event.data.user_id;
        set((state) => ({
          activeUsers: Array.from(new Set([...state.activeUsers, userId])),
        }));
      });

      client.on(EventType.USER_LEFT, (event) => {
        const userId = event.data.user_id;
        set((state) => ({
          activeUsers: state.activeUsers.filter((u) => u !== userId),
        }));
      });

      client.on(EventType.ERROR, (event) => {
        console.error('WebSocket error:', event.data);
        set({ error: event.data.error || 'Unknown error' });
      });

      // Connect to server
      await client.connect();

      set({
        isConnected: true,
        isConnecting: false,
        workspaceId,
        client,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Connection failed';
      set({
        isConnecting: false,
        error: message,
      });
      throw error;
    }
  },

  disconnect: () => {
    const { client } = get();
    if (client) {
      client.disconnect();
    }

    set({
      isConnected: false,
      client: null,
      workspaceId: null,
      activeUsers: [],
    });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setActiveUsers: (users: string[]) => {
    set({ activeUsers: users });
  },

  addUser: (userId: string) => {
    set((state) => ({
      activeUsers: Array.from(new Set([...state.activeUsers, userId])),
    }));
  },

  removeUser: (userId: string) => {
    set((state) => ({
      activeUsers: state.activeUsers.filter((u) => u !== userId),
    }));
  },
}));
