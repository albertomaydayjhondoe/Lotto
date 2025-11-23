/**
 * @jest-environment jsdom
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useOverviewAnalytics,
  useTimelineAnalytics,
  useHeatmapAnalytics,
  usePlatformAnalytics,
  useClipsAnalytics,
  useCampaignAnalytics,
  usePrefetchAnalytics,
  analyticsKeys,
} from '@/lib/visual_analytics/hooks';
import { visualAnalyticsApi } from '@/lib/visual_analytics/api';

// Mock API
jest.mock('@/lib/visual_analytics/api');

describe('Visual Analytics Hooks', () => {
  let queryClient: QueryClient;
  let wrapper: ({ children }: { children: ReactNode }) => JSX.Element;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    jest.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('useOverviewAnalytics', () => {
    it('should fetch overview data successfully', async () => {
      const mockData = {
        total_clips: 100,
        total_jobs: 50,
        total_publications: 75,
        total_campaigns: 10,
        clips_per_week: 15,
        clips_per_month: 60,
        average_clip_score: 85.5,
        top_clips: [],
        correlations: {},
        rule_engine_metrics: {},
        generated_at: '2024-01-15T10:00:00Z',
      };

      (visualAnalyticsApi.getOverview as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useOverviewAnalytics({ days: 30 }), {
        wrapper,
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
      expect(visualAnalyticsApi.getOverview).toHaveBeenCalledWith({ days: 30 });
    });

    it('should handle errors', async () => {
      const error = new Error('Network error');
      (visualAnalyticsApi.getOverview as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useOverviewAnalytics(), { wrapper });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should use correct cache key', async () => {
      const mockData = { total_clips: 100 };
      (visualAnalyticsApi.getOverview as jest.Mock).mockResolvedValue(mockData);

      const params = { days: 30, platform: 'instagram' };
      const { result } = renderHook(() => useOverviewAnalytics(params), {
        wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const cacheKey = analyticsKeys.overview(params);
      const cachedData = queryClient.getQueryData(cacheKey);

      expect(cachedData).toEqual(mockData);
    });
  });

  describe('useTimelineAnalytics', () => {
    it('should fetch timeline data successfully', async () => {
      const mockData = {
        jobs_timeline: [
          { timestamp: '2024-01-01T00:00:00Z', value: 10 },
          { timestamp: '2024-01-02T00:00:00Z', value: 15 },
        ],
        publications_timeline: [],
        clips_timeline: [],
        orchestrator_timeline: [],
      };

      (visualAnalyticsApi.getTimeline as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useTimelineAnalytics({ days: 7 }), {
        wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockData);
      expect(visualAnalyticsApi.getTimeline).toHaveBeenCalledWith({ days: 7 });
    });

    it('should handle empty timeline data', async () => {
      const mockData = {
        jobs_timeline: [],
        publications_timeline: [],
        clips_timeline: [],
        orchestrator_timeline: [],
      };

      (visualAnalyticsApi.getTimeline as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useTimelineAnalytics(), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockData);
    });
  });

  describe('useHeatmapAnalytics', () => {
    it('should fetch heatmap data successfully', async () => {
      const mockData = {
        metric: 'clips',
        data: [
          { hour: 0, day: 0, value: 5 },
          { hour: 1, day: 0, value: 10 },
        ],
      };

      (visualAnalyticsApi.getHeatmap as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useHeatmapAnalytics({ days: 7 }), {
        wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockData);
      expect(visualAnalyticsApi.getHeatmap).toHaveBeenCalledWith({ days: 7 });
    });
  });

  describe('usePlatformAnalytics', () => {
    it('should fetch platform stats successfully', async () => {
      const mockData = {
        total_platforms: 3,
        platforms: [
          { platform: 'instagram', clips_count: 50, publications_count: 40 },
          { platform: 'tiktok', clips_count: 30, publications_count: 25 },
          { platform: 'youtube', clips_count: 20, publications_count: 15 },
        ],
        best_platform: 'instagram',
      };

      (visualAnalyticsApi.getPlatformStats as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => usePlatformAnalytics({ days: 30 }), {
        wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockData);
      expect(visualAnalyticsApi.getPlatformStats).toHaveBeenCalledWith({ days: 30 });
    });

    it('should handle platform filter', async () => {
      const mockData = { total_platforms: 1, platforms: [], best_platform: null };
      (visualAnalyticsApi.getPlatformStats as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(
        () => usePlatformAnalytics({ days: 30, platform: 'instagram' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(visualAnalyticsApi.getPlatformStats).toHaveBeenCalledWith({
        days: 30,
        platform: 'instagram',
      });
    });
  });

  describe('useClipsAnalytics', () => {
    it('should fetch clips distribution successfully', async () => {
      const mockData = {
        total_clips: 100,
        duration_distribution: [
          { bucket: '0-30', count: 20 },
          { bucket: '30-60', count: 50 },
          { bucket: '60-120', count: 30 },
        ],
        score_distribution: [
          { bucket: '0-20', count: 5 },
          { bucket: '20-40', count: 10 },
          { bucket: '40-60', count: 25 },
          { bucket: '60-80', count: 35 },
          { bucket: '80-100', count: 25 },
        ],
        top_clips: [],
        average_score: 85.5,
        average_duration_seconds: 120,
      };

      (visualAnalyticsApi.getClipsDistribution as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useClipsAnalytics({ days: 30 }), {
        wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockData);
      expect(visualAnalyticsApi.getClipsDistribution).toHaveBeenCalledWith({
        days: 30,
      });
    });
  });

  describe('useCampaignAnalytics', () => {
    it('should fetch campaign breakdown successfully', async () => {
      const mockData = {
        total_campaigns: 10,
        active_campaigns: 5,
        campaigns: [
          {
            campaign_id: 'c1',
            name: 'Campaign 1',
            clips_count: 20,
            publications_count: 15,
            avg_score: 85.5,
            status: 'active',
            created_at: '2024-01-01T00:00:00Z',
          },
        ],
        avg_clips_per_campaign: 10,
      };

      (visualAnalyticsApi.getCampaignBreakdown as jest.Mock).mockResolvedValue(
        mockData
      );

      const { result } = renderHook(() => useCampaignAnalytics({ days: 30 }), {
        wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockData);
      expect(visualAnalyticsApi.getCampaignBreakdown).toHaveBeenCalledWith({
        days: 30,
      });
    });
  });

  describe('usePrefetchAnalytics', () => {
    it('should prefetch overview analytics', async () => {
      const mockData = { total_clips: 100 };
      (visualAnalyticsApi.getOverview as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => usePrefetchAnalytics(), { wrapper });

      // Prefetch data
      await result.current({ days: 30 });

      // Wait for prefetch to complete
      await waitFor(() => {
        const cacheKey = analyticsKeys.overview({ days: 30 });
        const cachedData = queryClient.getQueryData(cacheKey);
        return cachedData !== undefined;
      });

      const cacheKey = analyticsKeys.overview({ days: 30 });
      const cachedData = queryClient.getQueryData(cacheKey);

      expect(cachedData).toEqual(mockData);
      expect(visualAnalyticsApi.getOverview).toHaveBeenCalledWith({ days: 30 });
    });
  });

  describe('analyticsKeys', () => {
    it('should generate correct cache keys', () => {
      const overviewKey = analyticsKeys.overview({ days: 30 });
      expect(overviewKey).toEqual(['analytics', 'overview', { days: 30 }]);

      const timelineKey = analyticsKeys.timeline({ days: 7, platform: 'instagram' });
      expect(timelineKey).toEqual([
        'analytics',
        'timeline',
        { days: 7, platform: 'instagram' },
      ]);

      const heatmapKey = analyticsKeys.heatmap({});
      expect(heatmapKey).toEqual(['analytics', 'heatmap', {}]);
    });

    it('should generate unique keys for different params', () => {
      const key1 = analyticsKeys.overview({ days: 30 });
      const key2 = analyticsKeys.overview({ days: 60 });

      expect(key1).not.toEqual(key2);
    });
  });

  describe('conditional fetching', () => {
    it('should support enabled option', async () => {
      const mockData = { total_clips: 100 };
      (visualAnalyticsApi.getOverview as jest.Mock).mockResolvedValue(mockData);

      const { result, rerender } = renderHook(
        ({ enabled }: { enabled: boolean }) =>
          useOverviewAnalytics({ days: 30 }, enabled),
        {
          wrapper,
          initialProps: { enabled: false },
        }
      );

      // Should not fetch when disabled
      expect(result.current.isLoading).toBe(false);
      expect(visualAnalyticsApi.getOverview).not.toHaveBeenCalled();

      // Enable fetching
      rerender({ enabled: true });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(visualAnalyticsApi.getOverview).toHaveBeenCalledWith({ days: 30 });
    });
  });
});
