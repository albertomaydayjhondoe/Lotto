/**
 * AI Integration API Client
 * 
 * API functions for AI Global Worker integration (PASO 8.0).
 * Consumes dashboard-optimized AI reasoning endpoints.
 */

import { apiClient } from "@/lib/api"

/**
 * Health Card Types
 */
export interface AIHealthCard {
  score: number
  status: "critical" | "warning" | "healthy"
  status_label: string
  top_issue: string
  color: "red" | "yellow" | "green"
  overall_health: string
}

/**
 * Recommendation Card Types
 */
export interface AIRecommendationCard {
  category: string
  priority: string
  title: string
  description: string
  full_description: string
  impact: string
  effort: string
  badge_color: string
}

/**
 * Action Summary Types
 */
export interface AIActionSummary {
  total_steps: number
  estimated_duration: string
  risk_level: string
  automated: boolean
  objective: string
  risk_badge_color: string
  steps: Array<Record<string, any>>
}

/**
 * Snapshot Minimal Types
 */
export interface AISnapshotMinimal {
  clips_ready: number
  clips_pending_analysis: number
  jobs_pending: number
  jobs_failed: number
  campaigns_active: number
  campaigns_draft: number
}

/**
 * Dashboard AI Response Types
 */
export interface DashboardAIResponse {
  reasoning_id: string
  timestamp: string
  execution_time_ms: number
  health_card: AIHealthCard
  recommendations_cards: AIRecommendationCard[]
  actions_summary: AIActionSummary
  raw: {
    summary: {
      overall_health: string
      health_score: number
      key_insights: string[]
      concerns: string[]
      positives: string[]
    }
    snapshot: AISnapshotMinimal
  }
}

/**
 * AI Integration API Functions
 */
export const aiIntegrationApi = {
  /**
   * Get last AI reasoning output (dashboard format)
   */
  getLastAIReasoning: async (): Promise<DashboardAIResponse> => {
    const { data } = await apiClient.get("/dashboard/ai-integration/last")
    return data
  },

  /**
   * Trigger manual AI reasoning (dashboard format)
   */
  runAIReasoning: async (): Promise<DashboardAIResponse> => {
    const { data } = await apiClient.get("/dashboard/ai-integration/run")
    return data
  },

  /**
   * Get AI reasoning history (stub)
   */
  getAIHistory: async (): Promise<any[]> => {
    const { data } = await apiClient.get("/dashboard/ai-integration/history")
    return data
  },
}
