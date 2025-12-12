/**
 * AI History Types
 * 
 * TypeScript interfaces for AI Memory Layer (PASO 8.1/8.2).
 */

/**
 * AI History Item (Summary view)
 */
export interface AIHistoryItem {
  id: string
  created_at: string
  run_id: string
  health_score: number
  status: "ok" | "degraded" | "critical"
  critical_issues_count: number
  recommendations_count: number
  triggered_by: "worker" | "manual" | "debug"
  duration_ms: number
}

/**
 * AI History Item (Detail view)
 */
export interface AIHistoryItemDetail extends AIHistoryItem {
  snapshot: AISnapshot
  summary: AISummary
  recommendations: AIRecommendation[]
  action_plan: AIActionPlan
  meta: Record<string, any>
}

/**
 * System Snapshot
 */
export interface AISnapshot {
  timestamp: string
  queue_pending: number
  queue_processing: number
  queue_failed: number
  clips_ready: number
  clips_published: number
  jobs_pending: number
  jobs_completed: number
  campaigns_active: number
  campaigns_paused: number
  alerts_critical: number
  alerts_warning: number
  system_errors_recent: string[]
}

/**
 * AI Summary
 */
export interface AISummary {
  overall_health: string
  health_score: number
  key_insights: string[]
  concerns: string[]
  positives: string[]
  generated_at: string
}

/**
 * AI Recommendation
 */
export interface AIRecommendation {
  id: string
  priority: "critical" | "high" | "medium" | "low"
  category: string
  title: string
  description: string
  impact: string
  effort: string
  action_type?: string | null
  action_payload?: Record<string, any> | null
}

/**
 * AI Action Plan
 */
export interface AIActionPlan {
  plan_id: string
  title: string
  objective: string
  steps: Array<{ step: number; action: string; duration: string }>
  estimated_duration: string
  risk_level: string
  automated: boolean
}

/**
 * History Filters
 */
export interface AIHistoryFilters {
  limit?: number
  offset?: number
  min_score?: number
  max_score?: number
  status?: "ok" | "degraded" | "critical"
  only_critical?: boolean
  from_date?: string
  to_date?: string
}

/**
 * History Response
 */
export interface AIHistoryResponse {
  items: AIHistoryItem[]
  total: number
  limit: number
  offset: number
}
