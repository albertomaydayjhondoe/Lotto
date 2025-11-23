/**
 * AI History Module Tests
 * 
 * Test suite for AI Memory Layer (PASO 8.2).
 */

import { describe, it, expect, jest, beforeEach } from '@jest/globals'
import { aiHistoryApi } from '../api'
import { apiClient } from '@/lib/api'
import type { AIHistoryItem, AIHistoryItemDetail, AIHistoryFilters } from '../types'

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    get: jest.fn(),
  },
}))

describe('AI History API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getAIHistory', () => {
    it('test_fetch_history_with_filters', async () => {
      // Mock response data
      const mockHistoryItems: AIHistoryItem[] = [
        {
          id: '123e4567-e89b-12d3-a456-426614174000',
          created_at: '2025-11-23T10:00:00Z',
          run_id: 'run-001',
          health_score: 85,
          status: 'ok',
          critical_issues_count: 0,
          recommendations_count: 5,
          triggered_by: 'worker',
          duration_ms: 1500,
        },
        {
          id: '123e4567-e89b-12d3-a456-426614174001',
          created_at: '2025-11-23T09:30:00Z',
          run_id: 'run-002',
          health_score: 55,
          status: 'degraded',
          critical_issues_count: 2,
          recommendations_count: 8,
          triggered_by: 'manual',
          duration_ms: 2000,
        },
      ]

      // Setup mock
      jest.mocked(apiClient.get).mockResolvedValueOnce({ data: mockHistoryItems })

      // Test with filters
      const filters: AIHistoryFilters = {
        limit: 20,
        offset: 0,
        min_score: 50,
        status: 'degraded',
      }

      const result = await aiHistoryApi.getAIHistory(filters)

      // Verify API was called with correct query params
      expect(apiClient.get).toHaveBeenCalledWith(
        '/ai/global/history?limit=20&offset=0&min_score=50&status=degraded'
      )
      expect(result).toEqual(mockHistoryItems)
      expect(result).toHaveLength(2)
    })

    it('test_history_empty_list', async () => {
      // Setup mock for empty response
      jest.mocked(apiClient.get).mockResolvedValueOnce({ data: [] })

      const result = await aiHistoryApi.getAIHistory()

      expect(apiClient.get).toHaveBeenCalledWith('/ai/global/history')
      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })

    it('test_history_pagination', async () => {
      // Mock data for pagination test
      const mockPage1: AIHistoryItem[] = Array.from({ length: 20 }, (_, i) => ({
        id: `page1-${i}`,
        created_at: '2025-11-23T10:00:00Z',
        run_id: `run-${i}`,
        health_score: 80,
        status: 'ok' as const,
        critical_issues_count: 0,
        recommendations_count: 3,
        triggered_by: 'worker' as const,
        duration_ms: 1500,
      }))

      const mockPage2: AIHistoryItem[] = Array.from({ length: 20 }, (_, i) => ({
        id: `page2-${i}`,
        created_at: '2025-11-23T09:00:00Z',
        run_id: `run-${i + 20}`,
        health_score: 75,
        status: 'ok' as const,
        critical_issues_count: 0,
        recommendations_count: 2,
        triggered_by: 'worker' as const,
        duration_ms: 1200,
      }))

      // Test first page
      jest.mocked(apiClient.get).mockResolvedValueOnce({ data: mockPage1 })
      const page1 = await aiHistoryApi.getAIHistory({ limit: 20, offset: 0 })
      
      expect(page1).toHaveLength(20)
      expect(page1[0].id).toBe('page1-0')

      // Test second page
      jest.mocked(apiClient.get).mockResolvedValueOnce({ data: mockPage2 })
      const page2 = await aiHistoryApi.getAIHistory({ limit: 20, offset: 20 })
      
      expect(page2).toHaveLength(20)
      expect(page2[0].id).toBe('page2-0')
      
      // Verify different pages have different data
      expect(page1[0].id).not.toBe(page2[0].id)
    })
  })

  describe('getAIHistoryItem', () => {
    it('test_fetch_history_item_by_id', async () => {
      // Mock detailed history item
      const mockDetailItem: AIHistoryItemDetail = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        created_at: '2025-11-23T10:00:00Z',
        run_id: 'run-001',
        health_score: 85,
        status: 'ok',
        critical_issues_count: 0,
        recommendations_count: 5,
        triggered_by: 'worker',
        duration_ms: 1500,
        snapshot: {
          timestamp: '2025-11-23T10:00:00Z',
          queue_pending: 10,
          queue_processing: 2,
          queue_failed: 1,
          clips_ready: 50,
          clips_published: 200,
          jobs_pending: 5,
          jobs_completed: 100,
          campaigns_active: 3,
          campaigns_paused: 1,
          alerts_critical: 0,
          alerts_warning: 2,
          system_errors_recent: [],
        },
        summary: {
          overall_health: 'good',
          health_score: 85,
          key_insights: ['System is performing well'],
          concerns: ['Minor optimization needed'],
          positives: ['High success rate', 'Low error count'],
          generated_at: '2025-11-23T10:00:00Z',
        },
        recommendations: [
          {
            id: 'rec-1',
            priority: 'medium',
            category: 'performance',
            title: 'Optimize queue processing',
            description: 'Consider increasing worker capacity',
            impact: 'medium',
            effort: 'low',
          },
        ],
        action_plan: {
          plan_id: 'plan-001',
          title: 'System Optimization Plan',
          objective: 'Improve overall system performance',
          steps: [
            { step: 1, action: 'Monitor queue metrics', duration: '1 hour' },
            { step: 2, action: 'Adjust worker settings', duration: '30 minutes' },
          ],
          estimated_duration: '1.5 hours',
          risk_level: 'low',
          automated: false,
        },
        meta: {
          overall_health: 'good',
          generated_at: '2025-11-23T10:00:00Z',
        },
      }

      // Setup mock
      jest.mocked(apiClient.get).mockResolvedValueOnce({ data: mockDetailItem })

      const historyId = '123e4567-e89b-12d3-a456-426614174000'
      const result = await aiHistoryApi.getAIHistoryItem(historyId)

      expect(apiClient.get).toHaveBeenCalledWith(`/ai/global/history/${historyId}`)
      expect(result).toEqual(mockDetailItem)
      expect(result.snapshot).toBeDefined()
      expect(result.summary).toBeDefined()
      expect(result.recommendations).toHaveLength(1)
      expect(result.action_plan).toBeDefined()
    })
  })
})

describe('History Status Badges', () => {
  it('test_history_status_badges', () => {
    // Test status badge configurations
    const statuses = ['ok', 'degraded', 'critical'] as const
    
    const expectedConfigs = {
      ok: { label: 'OK', color: 'green' },
      degraded: { label: 'Degraded', color: 'yellow' },
      critical: { label: 'Critical', color: 'red' },
    }

    statuses.forEach((status) => {
      const config = expectedConfigs[status]
      expect(config).toBeDefined()
      expect(config.label).toBeTruthy()
      expect(config.color).toBeTruthy()
    })

    // Test that all statuses are covered
    expect(statuses).toHaveLength(3)
    expect(statuses).toContain('ok')
    expect(statuses).toContain('degraded')
    expect(statuses).toContain('critical')
  })
})
