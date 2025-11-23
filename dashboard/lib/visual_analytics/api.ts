/**
 * Visual Analytics API Client (PASO 8.4)
 * 
 * Provides typed functions to fetch analytics data from backend endpoints.
 */

import type {
  AnalyticsOverview,
  TimelineData,
  HeatmapData,
  PlatformStats,
  ClipsDistribution,
  CampaignBreakdown,
  AnalyticsQueryParams,
  HeatmapQueryParams,
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ANALYTICS_PREFIX = '/visual/analytics';

/**
 * Helper function to build query string from params
 */
function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  
  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

/**
 * Helper function to fetch with authentication
 */
async function fetchWithAuth<T>(endpoint: string): Promise<T> {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get complete analytics overview
 * 
 * @param params Query parameters (days_back)
 * @returns Complete analytics overview with all metrics
 */
export async function getOverview(
  params: AnalyticsQueryParams = {}
): Promise<AnalyticsOverview> {
  const queryString = buildQueryString({
    days_back: params.days_back ?? 30,
  });
  
  return fetchWithAuth<AnalyticsOverview>(
    `${ANALYTICS_PREFIX}/overview${queryString}`
  );
}

/**
 * Get timeline data for jobs, publications, clips
 * 
 * @param params Query parameters (days_back)
 * @returns Timeline data with multiple series
 */
export async function getTimeline(
  params: AnalyticsQueryParams = {}
): Promise<TimelineData> {
  const queryString = buildQueryString({
    days_back: params.days_back ?? 7,
  });
  
  return fetchWithAuth<TimelineData>(
    `${ANALYTICS_PREFIX}/timeline${queryString}`
  );
}

/**
 * Get activity heatmap by hour and day of week
 * 
 * @param params Query parameters (metric, days_back)
 * @returns Heatmap data structure
 */
export async function getHeatmap(
  params: HeatmapQueryParams = {}
): Promise<HeatmapData> {
  const queryString = buildQueryString({
    metric: params.metric ?? 'clips',
    days_back: params.days_back ?? 30,
  });
  
  return fetchWithAuth<HeatmapData>(
    `${ANALYTICS_PREFIX}/heatmap${queryString}`
  );
}

/**
 * Get platform performance breakdown
 * 
 * @param params Query parameters (days_back)
 * @returns Platform statistics
 */
export async function getPlatformStats(
  params: AnalyticsQueryParams = {}
): Promise<PlatformStats> {
  const queryString = buildQueryString({
    days_back: params.days_back ?? 30,
  });
  
  return fetchWithAuth<PlatformStats>(
    `${ANALYTICS_PREFIX}/platforms${queryString}`
  );
}

/**
 * Get clips distributions and rankings
 * 
 * @param params Query parameters (days_back)
 * @returns Clips distribution data
 */
export async function getClipsDistribution(
  params: AnalyticsQueryParams = {}
): Promise<ClipsDistribution> {
  const queryString = buildQueryString({
    days_back: params.days_back ?? 30,
  });
  
  return fetchWithAuth<ClipsDistribution>(
    `${ANALYTICS_PREFIX}/clips${queryString}`
  );
}

/**
 * Get campaign performance breakdown
 * 
 * @param params Query parameters (days_back)
 * @returns Campaign breakdown data
 */
export async function getCampaignBreakdown(
  params: AnalyticsQueryParams = {}
): Promise<CampaignBreakdown> {
  const queryString = buildQueryString({
    days_back: params.days_back ?? 30,
  });
  
  return fetchWithAuth<CampaignBreakdown>(
    `${ANALYTICS_PREFIX}/campaigns${queryString}`
  );
}

/**
 * Export all API functions
 */
export const visualAnalyticsApi = {
  getOverview,
  getTimeline,
  getHeatmap,
  getPlatformStats,
  getClipsDistribution,
  getCampaignBreakdown,
};

export default visualAnalyticsApi;
