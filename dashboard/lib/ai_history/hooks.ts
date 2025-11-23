/**
 * AI History React Query Hooks
 * 
 * Custom hooks for AI Memory Layer (PASO 8.1/8.2).
 */

import { useQuery } from "@tanstack/react-query"
import { aiHistoryApi } from "./api"
import type { AIHistoryItem, AIHistoryItemDetail, AIHistoryFilters } from "./types"

/**
 * Hook to fetch AI reasoning history
 * 
 * Fetches historical AI reasoning runs with optional filters.
 * Automatically refetches every 60 seconds.
 * 
 * @param filters - Filter and pagination options
 */
export function useAIHistory(filters: AIHistoryFilters = {}) {
  return useQuery<AIHistoryItem[], Error>({
    queryKey: ["ai-history", "list", filters],
    queryFn: () => aiHistoryApi.getAIHistory(filters),
    refetchInterval: 60000, // Auto-refresh every 60 seconds
    staleTime: 60000, // Consider data fresh for 60 seconds
  })
}

/**
 * Hook to fetch single AI reasoning history item
 * 
 * Fetches full details of a specific AI reasoning run.
 * 
 * @param id - History item UUID
 */
export function useAIHistoryItem(id: string | null | undefined) {
  return useQuery<AIHistoryItemDetail, Error>({
    queryKey: ["ai-history", "item", id],
    queryFn: () => aiHistoryApi.getAIHistoryItem(id!),
    enabled: !!id, // Only run query if ID is provided
    refetchInterval: 60000,
    staleTime: 60000,
  })
}

/**
 * Hook to get AI history count
 * 
 * Returns the total number of history items (for sidebar badge).
 */
export function useAIHistoryCount() {
  return useQuery<number, Error>({
    queryKey: ["ai-history", "count"],
    queryFn: aiHistoryApi.getAIHistoryCount,
    refetchInterval: 120000, // Refresh every 2 minutes
    staleTime: 60000,
  })
}
