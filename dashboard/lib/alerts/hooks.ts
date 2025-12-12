/**
 * React Hooks for Alerts
 * 
 * Provides hooks for alert management and WebSocket updates.
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsApi, Alert, AlertsListResponse } from './api';

/**
 * Hook for fetching all alerts
 */
export function useAlerts(unreadOnly: boolean = false) {
  return useQuery<AlertsListResponse>({
    queryKey: ['alerts', unreadOnly],
    queryFn: () => alertsApi.getAlerts(unreadOnly),
    refetchInterval: 30000, // Refetch every 30s
  });
}

/**
 * Hook for fetching unread alerts only
 */
export function useUnreadAlerts() {
  return useQuery<AlertsListResponse>({
    queryKey: ['alerts', 'unread'],
    queryFn: () => alertsApi.getUnreadAlerts(),
    refetchInterval: 10000, // Refetch every 10s for unread
  });
}

/**
 * Hook for marking alert as read
 */
export function useMarkAlertRead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (alertId: string) => alertsApi.markAlertRead(alertId),
    onSuccess: () => {
      // Invalidate alerts queries to refetch
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
    },
  });
}

/**
 * Hook for triggering manual analysis
 */
export function useRunAnalysis() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => alertsApi.runAnalysis(),
    onSuccess: () => {
      // Invalidate alerts queries to refetch
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

/**
 * Hook for alert stats (unread count)
 */
export function useAlertStats() {
  return useQuery({
    queryKey: ['alert-stats'],
    queryFn: () => alertsApi.getStats(),
    refetchInterval: 5000, // Refetch every 5s
  });
}

/**
 * Hook for WebSocket-based real-time alerts
 */
export function useAlertsWebSocket(onNewAlert?: (alert: Alert) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastAlert, setLastAlert] = useState<Alert | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/alerting/ws/alerts`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Alert WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const alert: Alert = JSON.parse(event.data);
        console.log('New alert received:', alert);
        
        setLastAlert(alert);
        
        // Call callback if provided
        if (onNewAlert) {
          onNewAlert(alert);
        }
        
        // Invalidate queries to refetch alerts
        queryClient.invalidateQueries({ queryKey: ['alerts'] });
        queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
      } catch (error) {
        console.error('Failed to parse alert:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Alert WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('Alert WebSocket disconnected');
      setIsConnected(false);
    };

    // Send ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);

    // Cleanup
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [onNewAlert, queryClient]);

  return {
    isConnected,
    lastAlert,
  };
}
