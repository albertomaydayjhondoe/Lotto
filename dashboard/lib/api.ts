import axios from "axios"

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

// Types from backend PASO 6.1
export interface OverviewStats {
  total_videos: number
  total_clips: number
  total_publications: number
  pending_publications: number
  active_jobs: number
  active_campaigns: number
  avg_processing_time_ms: number
  success_rate: number
  failed_publications: number
  avg_visual_score: number
}

export interface QueueStats {
  total_in_queue: number
  pending: number
  scheduled: number
  processing: number
  avg_wait_time_ms: number
  estimated_completion_time: string | null
}

export interface OrchestratorStats {
  total_jobs: number
  pending_jobs: number
  processing_jobs: number
  completed_jobs: number
  saturation_rate: number
}

export interface PlatformBreakdown {
  platform: string
  clips_ready: number
  posts_published: number
  posts_pending: number
  avg_visual_score: number
  success_rate: number
}

export interface PlatformStats {
  instagram: PlatformBreakdown
  tiktok: PlatformBreakdown
  youtube: PlatformBreakdown
  facebook: PlatformBreakdown
}

export interface CampaignStats {
  total: number
  draft: number
  scheduled: number
  published: number
  archived: number
}

// API functions
export const dashboardApi = {
  getOverview: async (): Promise<OverviewStats> => {
    const { data } = await apiClient.get("/dashboard/stats/overview")
    return data
  },

  getQueue: async (): Promise<QueueStats> => {
    const { data } = await apiClient.get("/dashboard/stats/queue")
    return data
  },

  getOrchestrator: async (): Promise<OrchestratorStats> => {
    const { data } = await apiClient.get("/dashboard/stats/orchestrator")
    return data
  },

  getPlatforms: async (): Promise<PlatformStats> => {
    const { data } = await apiClient.get("/dashboard/stats/platforms")
    return data
  },

  getCampaigns: async (): Promise<CampaignStats> => {
    const { data } = await apiClient.get("/dashboard/stats/campaigns")
    return data
  },
}
