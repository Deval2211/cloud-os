/**
 * WebSocket client for real-time events
 */

export enum EventType {
  // Session events
  SESSION_STARTED = 'session.started',
  SESSION_STOPPED = 'session.stopped',
  SESSION_ERROR = 'session.error',
  SESSION_STATUS_UPDATE = 'session.status_update',

  // Metrics events
  METRICS_UPDATE = 'metrics.update',
  GPU_USAGE = 'gpu.usage',
  MEMORY_USAGE = 'memory.usage',

  // Terminal events
  TERMINAL_OUTPUT = 'terminal.output',
  TERMINAL_INPUT = 'terminal.input',
  TERMINAL_RESIZE = 'terminal.resize',

  // Workflow events
  WORKFLOW_STARTED = 'workflow.started',
  WORKFLOW_STEP_COMPLETED = 'workflow.step_completed',
  WORKFLOW_STEP_FAILED = 'workflow.step_failed',
  WORKFLOW_COMPLETED = 'workflow.completed',

  // Collaboration events
  USER_JOINED = 'user.joined',
  USER_LEFT = 'user.left',
  CURSOR_UPDATE = 'cursor.update',

  // System events
  CONNECTION_ESTABLISHED = 'connection.established',
  HEARTBEAT = 'heartbeat',
  ERROR = 'error',
}

export interface WebSocketEvent {
  type: EventType;
  data: Record<string, any>;
  user_id?: string;
  workspace_id?: string;
  session_id?: string;
  timestamp: string;
}

export type EventHandler = (event: WebSocketEvent) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private workspaceId: string;
  private eventHandlers: Map<EventType, Set<EventHandler>> = new Map();
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    url: string,
    token: string,
    workspaceId: string
  ) {
    this.url = url;
    this.token = token;
    this.workspaceId = workspaceId;
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const wsUrl = apiUrl
          .replace('http://', 'ws://')
          .replace('https://', 'wss://');

        const connectionUrl = `${wsUrl}/ws/workspace/${this.workspaceId}?token=${this.token}`;

        this.ws = new WebSocket(connectionUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.stopHeartbeat();
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Send event to server
   */
  public sendEvent(event: WebSocketEvent): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    this.ws.send(JSON.stringify(event));
  }

  /**
   * Subscribe to event type
   */
  public on(eventType: EventType, handler: EventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }

    this.eventHandlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  /**
   * Unsubscribe from event type
   */
  public off(eventType: EventType, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * Check if connected
   */
  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(data: string): void {
    try {
      const event = JSON.parse(data) as WebSocketEvent;

      // Emit event to all listeners
      const handlers = this.eventHandlers.get(event.type as EventType);
      if (handlers) {
        handlers.forEach((handler) => handler(event));
      }

      // Also emit to wildcard listeners if we add that feature
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.sendEvent({
          type: EventType.HEARTBEAT,
          data: {},
          timestamp: new Date().toISOString(),
        });
      }
    }, 30000); // 30 seconds
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(
        `Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );

      setTimeout(() => {
        this.connect().catch(() => {
          // Retry will happen in next onclose
        });
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
}
