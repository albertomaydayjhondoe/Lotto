/**
 * AI History Detail Page
 * 
 * Displays detailed view of a single AI reasoning run (PASO 8.2).
 */

"use client"

import { useParams, useRouter } from "next/navigation"
import { useAIHistoryItem } from "@/lib/ai_history/hooks"
import { HistoryItemView } from "@/components/ai_history/HistoryItemView"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

export default function AIHistoryDetailPage() {
  const params = useParams()
  const router = useRouter()
  const historyId = params.id as string

  const { data: item, isLoading, error } = useAIHistoryItem(historyId)

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="text-gray-500 mt-4">Loading history details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-semibold">Failed to load history item</p>
          <p className="text-red-600 text-sm mt-1">{error.message}</p>
        </div>
        <Button
          onClick={() => router.back()}
          variant="outline"
          className="mt-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go Back
        </Button>
      </div>
    )
  }

  if (!item) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center py-12">
          <p className="text-gray-500">History item not found</p>
        </div>
        <Button
          onClick={() => router.back()}
          variant="outline"
          className="mt-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go Back
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <Button
        onClick={() => router.push("/dashboard/ai/history")}
        variant="outline"
        className="mb-6"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to History
      </Button>

      <HistoryItemView item={item} />
    </div>
  )
}
