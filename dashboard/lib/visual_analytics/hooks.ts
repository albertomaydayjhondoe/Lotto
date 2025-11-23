/**
 * React Query Hooks for Visual Analytics (PASO 8.4)
 * 
 * Custom hooks that wrap API calls with React Query for caching,
 * refetching, and state management.
 */

'use client';

import { useQuery, UseQueryResult } from '@tanstack/react-query';
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
import {
  getOverview,
  getTimeline,
  getHeatmap,
  getPlatformStats,
  getClipsDistribution,
  getCampaignBreakdown,
} from './api';

// Query keys for cache management
export const analyticsKeys = {
  all: ['visual-analytics'] as const,
  overview: (params: AnalyticsQueryParams) => 
    ['visual-analytics', 'overview', params] as const,
  timeline: (params: AnalyticsQueryParams) => 
    ['visual-analytics', 'timeline', params] as const,
  heatmap: (params: HeatmapQueryParams) => 
    ['visual-analytics', 'heatmap', params] as const,
  platforms: (params: AnalyticsQueryParams) => 
    ['visual-analytics', 'platforms', params] as const,
  clips: (params: AnalyticsQueryParams) => 
    ['visual-analytics', 'clips', params] as const,
  campaigns: (params: AnalyticsQueryParams) => 
    ['visual-analytics', 'campaigns', params] as const,
};

/**
 * Hook to fetch analytics overview
 * 
 * @param params Query parameters
 * @param options React Query options
 * @returns Query result with overview data
 */
export function useOverviewAnalytics(
  params: AnalyticsQueryParams = {},
  options: { enabled?: boolean } = {}
): UseQueryResult<AnalyticsOverview, Error> {
  return useQuery({
    queryKey: analyticsKeys.overview(params),
    queryFn: () => getOverview(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    refetchOnWindowFocus: false,
    enabled: options.enabled ?? true,
  });
}

/**
 * Hook to fetch timeline data
 * 
 * @param params Query parameters
 * @param options React Query options
 * @returns Query result with timeline data
 */
export function useTimelineAnalytics(
  params: AnalyticsQueryParams = {},
  options: { enabled?: boolean } = {}
): UseQueryResult<TimelineData, Error> {
  return useQuery({
    queryKey: analyticsKeys.timeline(params),
    queryFn: () => getTimeline(params),
    staleTime: 2 * 60 * 1000, // 2 minutes (fresher for timeline)
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: options.enabled ?? true,
  });
}

/**
 * Hook to fetch heatmap data
 * 
 * @param params Query parameters
 * @param options React Query options
 * @returns Query result with heatmap data
 */
export function useHeatmapAnalytics(
  params: HeatmapQueryParams = {},
  options: { enabled?: boolean } = {}
): UseQueryResult<HeatmapData, Error> {
  return useQuery({
    queryKey: analyticsKeys.heatmap(params),
    queryFn: () => getHeatmap(params),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: options.enabled ?? true,
  });
}

/**
 * Hook to fetch platform statistics
 * 
 * @param params Query parameters
 * @param options React Query options
 * @returns Query result with platform stats
 */
export function usePlatformAnalytics(
  params: AnalyticsQueryParams = {},
  options: { enabled?: boolean } = {}
): UseQueryResult<PlatformStats, Error> {
  return useQuery({
    queryKey: analyticsKeys.platforms(params),
    queryFn: () => getPlatformStats(params),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: options.enabled ?? true,
  });
}

/**
 * Hook to fetch clips distribution
 * 
 * @param params Query parameters
 * @param options React Query options
 * @returns Query result with clips distribution
 */
export function useClipsAnalytics(
  params: AnalyticsQueryParams = {},
  options: { enabled?: boolean } = {}
): UseQueryResult<ClipsDistribution, Error> {
  return useQuery({
    queryKey: analyticsKeys.clips(params),
    queryFn: () => getClipsDistribution(params),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: options.enabled ?? true,
  });
}

/**
 * Hook to fetch campaign breakdown
 * 
 * @param params Query parameters
 * @param options React Query options
 * @returns Query result with campaign breakdown
 */
export function useCampaignAnalytics(
  params: AnalyticsQueryParams = {},
  options: { enabled?: boolean } = {}
): UseQueryResult<CampaignBreakdown, Error> {
  return useQuery({
    queryKey: analyticsKeys.campaigns(params),
    queryFn: () => getCampaignBreakdown(params),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: options.enabled ?? true,
  });
}

/**
 * Hook to prefetch all analytics data
 * 
 * Useful for preloading data on navigation or user interaction
 */
export function usePrefetchAnalytics(params: AnalyticsQueryParams = {}) {
  const queryClient = useQuery({ queryKey: ['_'] }).client;
  
  return {
    prefetchOverview: () => 
      queryClient.prefetchQuery({
        queryKey: analyticsKeys.overview(params),
        queryFn: () => getOverview(params),
      }),
    prefetchTimeline: () => 
      queryClient.prefetchQuery({
        queryKey: analyticsKeys.timeline(params),
        queryFn: () => getTimeline(params),
      }),
    prefetchHeatmap: (heatmapParams: HeatmapQueryParams = {}) => 
      queryClient.prefetchQuery({
        queryKey: analyticsKeys.heatmap(heatmapParams),
        queryFn: () => getHeatmap(heatmapParams),
      }),
    prefetchPlatforms: () => 
      queryClient.prefetchQuery({
        queryKey: analyticsKeys.platforms(params),
        queryFn: () => getPlatformStats(params),
      }),
    prefetchClips: () => 
      queryClient.prefetchQuery({
        queryKey: analyticsKeys.clips(params),
        queryFn: () => getClipsDistribution(params),
      }),
    prefetchCampaigns: () => 
      queryClient.prefetchQuery({
        queryKey: analyticsKeys.campaigns(params),
        queryFn: () => getCampaignBreakdown(params),
      }),
  };
}
