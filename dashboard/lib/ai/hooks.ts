/**
 * AI React Query Hooks
 * 
 * Custom hooks for AI analysis, recommendations, and actions.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { aiApi, SystemAnalysis, Recommendation, ExecuteActionRequest, ExecuteActionResponse } from "./api"

/**
 * Hook to fetch system analysis
 */
export function useSystemAnalysis() {
  return useQuery({
    queryKey: ["ai", "analysis"],
    queryFn: aiApi.getAnalysis,
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

/**
 * Hook to fetch recommendations
 */
export function useRecommendations() {
  return useQuery({
    queryKey: ["ai", "recommendations"],
    queryFn: aiApi.getRecommendations,
    refetchInterval: 60000, // Refresh every minute
  })
}

/**
 * Hook to execute actions
 */
export function useExecuteAction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ExecuteActionRequest) => aiApi.executeAction(request),
    onSuccess: () => {
      // Invalidate related queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["ai"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

/**
 * Hook to force publish
 */
export function useForcePublish() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ clipId, platform, accountId }: { clipId: string; platform?: string; accountId?: string }) =>
      aiApi.forcePublish(clipId, platform, accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "queue"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to retry failed publications
 */
export function useRetryFailed() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => aiApi.retryFailed(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "queue"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to run orchestrator tick
 */
export function useRunOrchestrator() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => aiApi.runOrchestrator(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "orchestrator"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to run scheduler tick
 */
export function useRunScheduler() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (dryRun: boolean = false) => aiApi.runScheduler(dryRun),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to rebalance queue
 */
export function useRebalanceQueue() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => aiApi.rebalanceQueue(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "queue"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to promote clip
 */
export function usePromoteClip() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ videoId, campaignId }: { videoId: string; campaignId?: string }) =>
      aiApi.promoteClip(videoId, campaignId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "campaigns"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to publish best clip
 */
export function usePublishBestClip() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ videoId, platform }: { videoId: string; platform?: string }) =>
      aiApi.publishBestClip(videoId, platform),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to reschedule publication
 */
export function useReschedule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ logId, newTime }: { logId: string; newTime: string }) =>
      aiApi.reschedule(logId, newTime),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "queue"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to clear failed publications
 */
export function useClearFailed() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (olderThanDays: number = 7) => aiApi.clearFailed(olderThanDays),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "queue"] })
      queryClient.invalidateQueries({ queryKey: ["ai"] })
    },
  })
}

/**
 * Hook to generate system report
 */
export function useGenerateReport() {
  return useMutation({
    mutationFn: () => aiApi.generateReport(),
  })
}
