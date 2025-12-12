/**
 * AI Integration React Query Hooks
 * 
 * Custom hooks for AI Global Worker integration (PASO 8.0).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { aiIntegrationApi, DashboardAIResponse } from "./api"

/**
 * Hook to fetch last AI reasoning
 * 
 * Fetches the most recent AI reasoning output with dashboard formatting.
 * Automatically refetches every 2 minutes.
 */
export function useAIResult() {
  return useQuery<DashboardAIResponse>({
    queryKey: ["ai-integration", "last"],
    queryFn: aiIntegrationApi.getLastAIReasoning,
    refetchInterval: 120000, // Refresh every 2 minutes
    staleTime: 60000, // Consider data fresh for 1 minute
  })
}

/**
 * Hook to get AI recommendations
 * 
 * Extracts recommendations from the full AI reasoning output.
 */
export function useAIRecommendations() {
  const { data, ...rest } = useAIResult()
  
  return {
    data: data?.recommendations_cards,
    ...rest,
  }
}

/**
 * Hook to get AI summary
 * 
 * Extracts summary data from the full AI reasoning output.
 */
export function useAISummary() {
  const { data, ...rest } = useAIResult()
  
  return {
    data: data?.raw.summary,
    ...rest,
  }
}

/**
 * Hook to get AI action plan
 * 
 * Extracts action plan from the full AI reasoning output.
 */
export function useAIActionPlan() {
  const { data, ...rest } = useAIResult()
  
  return {
    data: data?.actions_summary,
    ...rest,
  }
}

/**
 * Hook to manually trigger AI reasoning
 * 
 * Triggers a new AI reasoning cycle and returns the result.
 * Automatically invalidates cached data on success.
 */
export function useAIManualRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: aiIntegrationApi.runAIReasoning,
    onSuccess: (data) => {
      // Update cache with new data
      queryClient.setQueryData(["ai-integration", "last"], data)
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["ai-integration"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

/**
 * Hook to fetch AI reasoning history
 * 
 * Currently returns empty array (stub implementation).
 * Future: Will support pagination and filtering.
 */
export function useAIHistory() {
  return useQuery({
    queryKey: ["ai-integration", "history"],
    queryFn: aiIntegrationApi.getAIHistory,
    staleTime: 300000, // 5 minutes
  })
}
