/**
 * Telemetry WebSocket Client
 * 
 * Manages WebSocket connection to the live telemetry endpoint with
 * automatic reconnection and exponential backoff.
 */

export interface QueueStats {
  pending: number;
  processing: number;
  success: number;
  failed: number;
  total: number;
}

export interface SchedulerStats {
  scheduled_today: number;
  scheduled_next_hour: number;
  overdue: number;
  avg_delay_seconds: number | null;
}

export interface OrchestratorStats {
  actions_last_minute: number;
  decisions_pending: number;
  saturation_rate: number | null;
  last_run_seconds_ago: number | null;
}

export interface PlatformStats {
  instagram: number;
  tiktok: number;
  youtube: number;
  facebook: number;
}

export interface WorkerStats {
  active_workers: number;
  tasks_processing: number;
  avg_processing_time_ms: number | null;
}

export interface TelemetryPayload {
  queue: QueueStats;
  scheduler: SchedulerStats;
  orchestrator: OrchestratorStats;
  platforms: PlatformStats;
  workers: WorkerStats;
  timestamp: string;
}

export type TelemetryMessageHandler = (payload: TelemetryPayload) => void;
export type TelemetryErrorHandler = (error: Event) => void;
export type TelemetryConnectionHandler = () => void;

interface TelemetrySocketConfig {
  url: string;
  reconnectDelay?: number;
  maxReconnectDelay?: number;
  reconnectDecay?: number;
  timeoutInterval?: number;
  maxReconnectAttempts?: number;
}

/**
 * WebSocket client for live telemetry streaming.
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Connection state management
 * - Error handling
 * - Ping/pong keepalive
 * 
 * Example:
 * ```typescript
 * const socket = new TelemetrySocket({
 *   url: 'ws://localhost:8000/telemetry/live/ws/telemetry'
 * });
 * 
 * socket.onMessage((data) => console.log('Telemetry:', data));
 * socket.onError((error) => console.error('Error:', error));
 * socket.connect();
 * ```
 */
export class TelemetrySocket {
  private ws: WebSocket | null = null;
  private config: Required<TelemetrySocketConfig>;
  private reconnectAttempts = 0;
  private reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private pingIntervalId: ReturnType<typeof setInterval> | null = null;
  private messageHandlers: TelemetryMessageHandler[] = [];
  private errorHandlers: TelemetryErrorHandler[] = [];
  private openHandlers: TelemetryConnectionHandler[] = [];
  private closeHandlers: TelemetryConnectionHandler[] = [];
  private shouldReconnect = true;

  constructor(config: TelemetrySocketConfig) {
    this.config = {
      url: config.url,
      reconnectDelay: config.reconnectDelay ?? 1000,
      maxReconnectDelay: config.maxReconnectDelay ?? 30000,
      reconnectDecay: config.reconnectDecay ?? 1.5,
      timeoutInterval: config.timeoutInterval ?? 30000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? Infinity,
    };
  }

  /**
   * Connect to the WebSocket server.
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('TelemetrySocket: Already connected');
      return;
    }

    try {
      this.ws = new WebSocket(this.config.url);
      this.setupEventListeners();
    } catch (error) {
      console.error('TelemetrySocket: Failed to create WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket server.
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.cleanup();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Register a message handler.
   */
  onMessage(handler: TelemetryMessageHandler): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  /**
   * Register an error handler.
   */
  onError(handler: TelemetryErrorHandler): () => void {
    this.errorHandlers.push(handler);
    return () => {
      this.errorHandlers = this.errorHandlers.filter(h => h !== handler);
    };
  }

  /**
   * Register an open (connected) handler.
   */
  onOpen(handler: TelemetryConnectionHandler): () => void {
    this.openHandlers.push(handler);
    return () => {
      this.openHandlers = this.openHandlers.filter(h => h !== handler);
    };
  }

  /**
   * Register a close (disconnected) handler.
   */
  onClose(handler: TelemetryConnectionHandler): () => void {
    this.closeHandlers.push(handler);
    return () => {
      this.closeHandlers = this.closeHandlers.filter(h => h !== handler);
    };
  }

  /**
   * Get current connection state.
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current reconnection attempt count.
   */
  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('TelemetrySocket: Connected');
      this.reconnectAttempts = 0;
      this.startPingInterval();
      this.openHandlers.forEach(handler => handler());
    };

    this.ws.onmessage = (event) => {
      try {
        const payload: TelemetryPayload = JSON.parse(event.data);
        this.messageHandlers.forEach(handler => handler(payload));
      } catch (error) {
        console.error('TelemetrySocket: Failed to parse message:', error);
      }
    };

    this.ws.onerror = (event) => {
      console.error('TelemetrySocket: Error:', event);
      this.errorHandlers.forEach(handler => handler(event));
    };

    this.ws.onclose = () => {
      console.log('TelemetrySocket: Disconnected');
      this.cleanup();
      this.closeHandlers.forEach(handler => handler());
      
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    };
  }

  private startPingInterval(): void {
    this.pingIntervalId = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        try {
          this.ws.send('ping');
        } catch (error) {
          console.error('TelemetrySocket: Failed to send ping:', error);
        }
      }
    }, this.config.timeoutInterval);
  }

  private cleanup(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
    
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('TelemetrySocket: Max reconnection attempts reached');
      return;
    }

    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(this.config.reconnectDecay, this.reconnectAttempts),
      this.config.maxReconnectDelay
    );

    console.log(`TelemetrySocket: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimeoutId = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }
}

/**
 * Create a TelemetrySocket instance with default configuration.
 */
export function createTelemetrySocket(baseUrl: string = 'ws://localhost:8000'): TelemetrySocket {
  const url = `${baseUrl}/telemetry/live/ws/telemetry`;
  return new TelemetrySocket({ url });
}
