/**
 * AI History API Client
 * 
 * API functions for AI Memory Layer (PASO 8.1/8.2).
 * Fetches historical AI reasoning runs with filtering and pagination.
 */

import { apiClient } from "@/lib/api"
import type { AIHistoryItem, AIHistoryItemDetail, AIHistoryFilters } from "./types"

/**
 * API Client for AI History endpoints
 */
export const aiHistoryApi = {
  /**
   * Get AI reasoning history with filters
   * 
   * @param filters - Filter and pagination options
   * @returns Array of history items
   */
  async getAIHistory(filters: AIHistoryFilters = {}): Promise<AIHistoryItem[]> {
    const params = new URLSearchParams()
    
    if (filters.limit !== undefined) params.append("limit", String(filters.limit))
    if (filters.offset !== undefined) params.append("offset", String(filters.offset))
    if (filters.min_score !== undefined) params.append("min_score", String(filters.min_score))
    if (filters.max_score !== undefined) params.append("max_score", String(filters.max_score))
    if (filters.status) params.append("status", filters.status)
    if (filters.only_critical !== undefined) params.append("only_critical", String(filters.only_critical))
    if (filters.from_date) params.append("from_date", filters.from_date)
    if (filters.to_date) params.append("to_date", filters.to_date)
    
    const queryString = params.toString()
    const url = queryString ? `/ai/global/history?${queryString}` : "/ai/global/history"
    
    const response = await apiClient.get<AIHistoryItem[]>(url)
    return response.data
  },

  /**
   * Get single AI reasoning history item by ID
   * 
   * @param id - History item UUID
   * @returns Full history item with details
   */
  async getAIHistoryItem(id: string): Promise<AIHistoryItemDetail> {
    const response = await apiClient.get<AIHistoryItemDetail>(`/ai/global/history/${id}`)
    return response.data
  },

  /**
   * Get history count (for sidebar badge)
   * 
   * @returns Total number of history items
   */
  async getAIHistoryCount(): Promise<number> {
    try {
      const response = await apiClient.get<AIHistoryItem[]>("/ai/global/history?limit=1")
      // Backend doesn't return total count yet, so we estimate based on having data
      return response.data.length > 0 ? 1 : 0
    } catch (error) {
      console.error("Failed to fetch AI history count:", error)
      return 0
    }
  },
}

export default aiHistoryApi
