/**
 * AI API Client
 * 
 * API functions for AI analysis, recommendations, and actions.
 */

import { apiClient } from "@/lib/api"

/**
 * System Analysis Types
 */
export interface SystemAnalysis {
  timestamp: string
  queue_health: "good" | "warning" | "critical"
  orchestrator_health: "good" | "warning" | "critical"
  campaigns_status: "good" | "warning" | "critical"
  publish_success_rate: number
  pending_scheduled: number
  best_clip_per_platform: Record<string, {
    clip_id: string
    variant_id: string
    score: number
    duration: number
    created_at: string | null
  }>
  issues_detected: Array<{
    severity: "info" | "warning" | "critical"
    title: string
    description: string
  }>
  metrics: {
    total_clips_ready: number
    avg_processing_time_ms: number | null
    platform_distribution: Record<string, number>
    total_in_queue: number
    failed_rate: number
  }
}

/**
 * Recommendation Types
 */
export interface Recommendation {
  id: string
  title: string
  description: string
  severity: "info" | "warning" | "critical"
  action: "publish" | "reschedule" | "promote" | "retry" | "run_orchestrator" | 
          "run_scheduler" | "rebalance_queue" | "publish_best_clip" | 
          "clear_failed" | "optimize_schedule"
  payload: Record<string, any>
  created_at: string
}

/**
 * Action Execution Types
 */
export interface ExecuteActionRequest {
  action: string
  payload: Record<string, any>
  recommendation_id?: string
}

export interface ExecuteActionResponse {
  success: boolean
  action: string
  message: string
  result: Record<string, any>
  executed_at: string
}

/**
 * AI API Functions
 */
export const aiApi = {
  /**
   * Get system analysis
   */
  getAnalysis: async (): Promise<SystemAnalysis> => {
    const { data } = await apiClient.get("/dashboard/ai/analyze")
    return data
  },

  /**
   * Get AI recommendations
   */
  getRecommendations: async (): Promise<Recommendation[]> => {
    const { data } = await apiClient.get("/dashboard/ai/recommendations")
    return data
  },

  /**
   * Execute an action
   */
  executeAction: async (request: ExecuteActionRequest): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/ai/execute", request)
    return data
  },

  /**
   * Force publish a clip
   */
  forcePublish: async (clipId: string, platform?: string, accountId?: string): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/force-publish", {
      clip_id: clipId,
      platform,
      account_id: accountId
    })
    return data
  },

  /**
   * Retry failed publications
   */
  retryFailed: async (): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/retry-failed")
    return data
  },

  /**
   * Run orchestrator tick
   */
  runOrchestrator: async (): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/run-orchestrator")
    return data
  },

  /**
   * Run scheduler tick
   */
  runScheduler: async (dryRun: boolean = false): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/run-scheduler", {
      dry_run: dryRun
    })
    return data
  },

  /**
   * Rebalance queue
   */
  rebalanceQueue: async (): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/rebalance-queue")
    return data
  },

  /**
   * Promote clip to campaign
   */
  promoteClip: async (videoId: string, campaignId?: string): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/promote-clip", {
      video_id: videoId,
      campaign_id: campaignId
    })
    return data
  },

  /**
   * Publish best clip
   */
  publishBestClip: async (videoId: string, platform?: string): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/publish-best-clip", {
      video_id: videoId,
      platform
    })
    return data
  },

  /**
   * Reschedule publication
   */
  reschedule: async (logId: string, newTime: string): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/reschedule", {
      log_id: logId,
      new_time: newTime
    })
    return data
  },

  /**
   * Clear failed publications
   */
  clearFailed: async (olderThanDays: number = 7): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/clear-failed", {
      older_than_days: olderThanDays
    })
    return data
  },

  /**
   * Generate system report
   */
  generateReport: async (): Promise<ExecuteActionResponse> => {
    const { data } = await apiClient.post("/dashboard/actions/generate-report")
    return data
  }
}
