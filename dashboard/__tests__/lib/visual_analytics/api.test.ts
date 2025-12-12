/**
 * @jest-environment jsdom
 */

import { visualAnalyticsApi } from '@/lib/visual_analytics/api';
import type { AnalyticsQueryParams } from '@/lib/visual_analytics/types';

// Mock fetch globally
global.fetch = jest.fn();

describe('visualAnalyticsApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock localStorage
    Storage.prototype.getItem = jest.fn(() => 'test-token-12345');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('getOverview', () => {
    it('should fetch overview with default params', async () => {
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

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await visualAnalyticsApi.getOverview();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/visual_analytics/overview'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token-12345',
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should fetch overview with query params', async () => {
      const mockData = { total_clips: 50 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const params: AnalyticsQueryParams = {
        days: 30,
        platform: 'instagram',
      };

      await visualAnalyticsApi.getOverview(params);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('days=30'),
        expect.any(Object)
      );
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('platform=instagram'),
        expect.any(Object)
      );
    });

    it('should throw error on HTTP error', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(visualAnalyticsApi.getOverview()).rejects.toThrow('HTTP 500');
    });

    it('should handle missing auth token', async () => {
      Storage.prototype.getItem = jest.fn(() => null);

      const mockData = { total_clips: 100 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      await visualAnalyticsApi.getOverview();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: '',
          }),
        })
      );
    });
  });

  describe('getTimeline', () => {
    it('should fetch timeline data', async () => {
      const mockData = {
        jobs_timeline: [],
        publications_timeline: [],
        clips_timeline: [],
        orchestrator_timeline: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await visualAnalyticsApi.getTimeline({ days: 7 });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/visual_analytics/timeline'),
        expect.any(Object)
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('getHeatmap', () => {
    it('should fetch heatmap data', async () => {
      const mockData = {
        metric: 'clips',
        data: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await visualAnalyticsApi.getHeatmap({ days: 7 });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/visual_analytics/heatmap'),
        expect.any(Object)
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('getPlatformStats', () => {
    it('should fetch platform stats', async () => {
      const mockData = {
        total_platforms: 3,
        platforms: [],
        best_platform: null,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await visualAnalyticsApi.getPlatformStats({ days: 30 });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/visual_analytics/platforms'),
        expect.any(Object)
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('getClipsDistribution', () => {
    it('should fetch clips distribution', async () => {
      const mockData = {
        total_clips: 100,
        duration_distribution: [],
        score_distribution: [],
        top_clips: [],
        average_score: 85.5,
        average_duration_seconds: 120,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await visualAnalyticsApi.getClipsDistribution({ days: 30 });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/visual_analytics/clips'),
        expect.any(Object)
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('getCampaignBreakdown', () => {
    it('should fetch campaign breakdown', async () => {
      const mockData = {
        total_campaigns: 10,
        active_campaigns: 5,
        campaigns: [],
        avg_clips_per_campaign: 10,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await visualAnalyticsApi.getCampaignBreakdown({ days: 30 });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/visual_analytics/campaigns'),
        expect.any(Object)
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('date range params', () => {
    it('should handle start_date and end_date', async () => {
      const mockData = { total_clips: 50 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const params: AnalyticsQueryParams = {
        start_date: '2024-01-01',
        end_date: '2024-01-31',
      };

      await visualAnalyticsApi.getOverview(params);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01'),
        expect.any(Object)
      );
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-01-31'),
        expect.any(Object)
      );
    });

    it('should handle all params together', async () => {
      const mockData = { total_clips: 50 };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const params: AnalyticsQueryParams = {
        days: 30,
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        platform: 'tiktok',
      };

      await visualAnalyticsApi.getOverview(params);

      const fetchUrl = (global.fetch as jest.Mock).mock.calls[0][0];
      expect(fetchUrl).toContain('days=30');
      expect(fetchUrl).toContain('start_date=2024-01-01');
      expect(fetchUrl).toContain('end_date=2024-01-31');
      expect(fetchUrl).toContain('platform=tiktok');
    });
  });
});
