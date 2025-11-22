"use client"

/**
 * AI Recommendations Page
 * 
 * Displays AI-generated recommendations with execution capability.
 */

import { useState } from "react"
import { useRecommendations, useExecuteAction } from "@/lib/ai/hooks"
import { RecommendationCard } from "@/components/ai/recommendation-card"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader } from "@/components/ui/loader"
import { Button } from "@/components/ui/button"
import { Recommendation } from "@/lib/ai/api"
import { RefreshCw, Lightbulb } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"

export default function RecommendationsPage() {
  const { data: recommendations, isLoading, error } = useRecommendations()
  const executeAction = useExecuteAction()
  const queryClient = useQueryClient()
  const [executingId, setExecutingId] = useState<string | null>(null)

  const handleExecute = async (recommendation: Recommendation) => {
    setExecutingId(recommendation.id)
    try {
      await executeAction.mutateAsync({
        action: recommendation.action,
        payload: recommendation.payload,
        recommendation_id: recommendation.id
      })
      
      // Show success (you could use a toast notification here)
      alert(`Action "${recommendation.action}" executed successfully!`)
    } catch (error) {
      // Show error
      alert(`Failed to execute action: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setExecutingId(null)
    }
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["ai", "recommendations"] })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-700">Error Loading Recommendations</CardTitle>
            <CardDescription className="text-red-600">
              {error instanceof Error ? error.message : "Failed to load recommendations"}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (!recommendations) {
    return null
  }

  // Group by severity
  const critical = recommendations.filter(r => r.severity === "critical")
  const warning = recommendations.filter(r => r.severity === "warning")
  const info = recommendations.filter(r => r.severity === "info")

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            AI Recommendations
          </h1>
          <p className="text-muted-foreground mt-2">
            Intelligent suggestions to optimize system performance
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {recommendations.length === 0 ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <div className="text-center">
                <Lightbulb className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">No recommendations at this time</p>
                <p className="text-sm">Your system is running optimally</p>
              </div>
            </div>
          </CardHeader>
        </Card>
      ) : (
        <>
          {/* Critical Recommendations */}
          {critical.length > 0 && (
            <div className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-red-600">Critical ({critical.length})</h2>
                <p className="text-sm text-muted-foreground">Immediate action required</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {critical.map((rec) => (
                  <RecommendationCard
                    key={rec.id}
                    recommendation={rec}
                    onExecute={handleExecute}
                    isExecuting={executingId === rec.id}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Warning Recommendations */}
          {warning.length > 0 && (
            <div className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-yellow-600">Warning ({warning.length})</h2>
                <p className="text-sm text-muted-foreground">Should be addressed soon</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {warning.map((rec) => (
                  <RecommendationCard
                    key={rec.id}
                    recommendation={rec}
                    onExecute={handleExecute}
                    isExecuting={executingId === rec.id}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Info Recommendations */}
          {info.length > 0 && (
            <div className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-blue-600">Suggestions ({info.length})</h2>
                <p className="text-sm text-muted-foreground">Optional optimizations</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {info.map((rec) => (
                  <RecommendationCard
                    key={rec.id}
                    recommendation={rec}
                    onExecute={handleExecute}
                    isExecuting={executingId === rec.id}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
