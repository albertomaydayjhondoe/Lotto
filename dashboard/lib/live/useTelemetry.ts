/**
 * React Hook for Live Telemetry
 * 
 * Provides real-time telemetry data via WebSocket connection.
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  TelemetrySocket, 
  TelemetryPayload, 
  createTelemetrySocket 
} from './socket';

export interface UseTelemetryOptions {
  /**
   * Base URL for WebSocket connection.
   * Defaults to ws://localhost:8000 in development.
   */
  baseUrl?: string;
  
  /**
   * Whether to automatically connect on mount.
   * Defaults to true.
   */
  autoConnect?: boolean;
  
  /**
   * Callback when connection is established.
   */
  onConnect?: () => void;
  
  /**
   * Callback when connection is closed.
   */
  onDisconnect?: () => void;
  
  /**
   * Callback when an error occurs.
   */
  onError?: (error: Event) => void;
}

export interface UseTelemetryResult {
  /**
   * Current telemetry data.
   */
  data: TelemetryPayload | null;
  
  /**
   * Whether the WebSocket is connected.
   */
  isConnected: boolean;
  
  /**
   * Whether this is the initial connection attempt.
   */
  isConnecting: boolean;
  
  /**
   * Current reconnection attempt count.
   */
  reconnectAttempts: number;
  
  /**
   * Timestamp of last received data.
   */
  lastUpdated: Date | null;
  
  /**
   * Manually trigger a reconnection.
   */
  reconnect: () => void;
  
  /**
   * Manually disconnect.
   */
  disconnect: () => void;
}

/**
 * Hook for consuming live telemetry data.
 * 
 * Example:
 * ```tsx
 * function MyComponent() {
 *   const { data, isConnected, lastUpdated } = useTelemetry();
 *   
 *   if (!isConnected) {
 *     return <div>Connecting to telemetry...</div>;
 *   }
 *   
 *   return (
 *     <div>
 *       <p>Queue Pending: {data?.queue.pending}</p>
 *       <p>Last Updated: {lastUpdated?.toLocaleTimeString()}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useTelemetry(options: UseTelemetryOptions = {}): UseTelemetryResult {
  const {
    baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    autoConnect = true,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [data, setData] = useState<TelemetryPayload | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(autoConnect);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  const socketRef = useRef<TelemetrySocket | null>(null);

  const handleMessage = useCallback((payload: TelemetryPayload) => {
    setData(payload);
    setLastUpdated(new Date());
  }, []);

  const handleOpen = useCallback(() => {
    setIsConnected(true);
    setIsConnecting(false);
    setReconnectAttempts(0);
    onConnect?.();
  }, [onConnect]);

  const handleClose = useCallback(() => {
    setIsConnected(false);
    onDisconnect?.();
  }, [onDisconnect]);

  const handleError = useCallback((error: Event) => {
    console.error('Telemetry WebSocket error:', error);
    onError?.(error);
  }, [onError]);

  const reconnect = useCallback(() => {
    if (socketRef.current) {
      setIsConnecting(true);
      socketRef.current.disconnect();
      socketRef.current.connect();
      setReconnectAttempts(prev => prev + 1);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      setIsConnected(false);
      setIsConnecting(false);
    }
  }, []);

  useEffect(() => {
    if (!autoConnect) return;

    // Create socket instance
    const socket = createTelemetrySocket(baseUrl);
    socketRef.current = socket;

    // Register handlers
    const unsubMessage = socket.onMessage(handleMessage);
    const unsubOpen = socket.onOpen(handleOpen);
    const unsubClose = socket.onClose(handleClose);
    const unsubError = socket.onError(handleError);

    // Connect
    socket.connect();

    // Cleanup on unmount
    return () => {
      unsubMessage();
      unsubOpen();
      unsubClose();
      unsubError();
      socket.disconnect();
      socketRef.current = null;
    };
  }, [baseUrl, autoConnect, handleMessage, handleOpen, handleClose, handleError]);

  return {
    data,
    isConnected,
    isConnecting,
    reconnectAttempts,
    lastUpdated,
    reconnect,
    disconnect,
  };
}

/**
 * Hook for specific telemetry metric.
 * 
 * Example:
 * ```tsx
 * function QueueMetric() {
 *   const queueData = useTelemetryMetric(data => data?.queue);
 *   return <div>Pending: {queueData?.pending}</div>;
 * }
 * ```
 */
export function useTelemetryMetric<T>(
  selector: (payload: TelemetryPayload | null) => T
): T {
  const { data } = useTelemetry();
  return selector(data);
}
