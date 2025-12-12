/**
 * AI History List Page
 * 
 * Displays paginated list of AI reasoning runs with filtering (PASO 8.2).
 */

"use client"

import { useState } from "react"
import { useAIHistory } from "@/lib/ai_history/hooks"
import { HistoryTable } from "@/components/ai_history/HistoryTable"
import { HistoryFilters } from "@/components/ai_history/HistoryFilters"
import { Button } from "@/components/ui/button"
import type { AIHistoryFilters, AIHistoryItem } from "@/lib/ai_history/types"

const ITEMS_PER_PAGE = 20

export default function AIHistoryPage() {
  const [filters, setFilters] = useState<AIHistoryFilters>({
    limit: ITEMS_PER_PAGE,
    offset: 0,
  })
  
  const [page, setPage] = useState(0)

  const { data: items, isLoading, error } = useAIHistory(filters)
  const historyItems = (items || []) as AIHistoryItem[]

  const handleFiltersChange = (newFilters: AIHistoryFilters) => {
    setFilters({
      ...newFilters,
      limit: ITEMS_PER_PAGE,
      offset: 0,
    })
    setPage(0)
  }

  const handleNextPage = () => {
    const newPage = page + 1
    setPage(newPage)
    setFilters({
      ...filters,
      offset: newPage * ITEMS_PER_PAGE,
    })
  }

  const handlePrevPage = () => {
    const newPage = Math.max(0, page - 1)
    setPage(newPage)
    setFilters({
      ...filters,
      offset: newPage * ITEMS_PER_PAGE,
    })
  }

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-semibold">Failed to load AI history</p>
          <p className="text-red-600 text-sm mt-1">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">AI Reasoning History</h1>
        <p className="text-gray-500 mt-2">
          Historical record of AI Global Worker reasoning runs and system analysis
        </p>
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div>
          <HistoryFilters 
            filters={filters} 
            onFiltersChange={handleFiltersChange} 
          />
        </div>

        {/* Main Content */}
        <div className="col-span-3">
          <HistoryTable
            items={historyItems}
            isLoading={isLoading}
          />          {/* Pagination */}
          {historyItems.length > 0 && (
            <div className="flex justify-between items-center mt-6">
              <div className="text-sm text-gray-500">
                Showing {page * ITEMS_PER_PAGE + 1} to {Math.min((page + 1) * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)} of many
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handlePrevPage}
                  disabled={page === 0}
                  variant="outline"
                >
                  Previous
                </Button>
                <Button
                  onClick={handleNextPage}
                  disabled={historyItems.length < ITEMS_PER_PAGE}
                  variant="outline"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
