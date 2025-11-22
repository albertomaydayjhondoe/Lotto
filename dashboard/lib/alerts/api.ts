/**
 * Alert API Client
 * 
 * API functions for alert management.
 */

export interface Alert {
  id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  metadata: Record<string, any>;
  created_at: string;
  read: boolean;
}

export interface AlertsListResponse {
  alerts: Alert[];
  total: number;
  unread_count: number;
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const alertsApi = {
  /**
   * Get all alerts
   */
  async getAlerts(unreadOnly: boolean = false, limit: number = 100): Promise<AlertsListResponse> {
    const url = `${BASE_URL}/alerting/alerts?unread_only=${unreadOnly}&limit=${limit}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return response.json();
  },

  /**
   * Get only unread alerts
   */
  async getUnreadAlerts(limit: number = 100): Promise<AlertsListResponse> {
    const url = `${BASE_URL}/alerting/alerts/unread?limit=${limit}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch unread alerts');
    return response.json();
  },

  /**
   * Mark alert as read
   */
  async markAlertRead(alertId: string): Promise<{ success: boolean; message: string }> {
    const url = `${BASE_URL}/alerting/alerts/${alertId}/read`;
    const response = await fetch(url, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to mark alert as read');
    return response.json();
  },

  /**
   * Manually trigger system analysis
   */
  async runAnalysis(): Promise<{ success: boolean; alerts_generated: number; alerts: Alert[] }> {
    const url = `${BASE_URL}/alerting/run-analysis`;
    const response = await fetch(url, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to run analysis');
    return response.json();
  },

  /**
   * Get alert statistics
   */
  async getStats(): Promise<{ unread_count: number; active_connections: number; has_subscribers: boolean }> {
    const url = `${BASE_URL}/alerting/stats`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  }
};
