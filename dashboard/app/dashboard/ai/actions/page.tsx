"use client"

/**
 * AI Actions Page
 * 
 * Manual action controls for dashboard operations.
 */

import {
  useRetryFailed,
  useRunOrchestrator,
  useRunScheduler,
  useRebalanceQueue,
  useClearFailed,
  useGenerateReport
} from "@/lib/ai/hooks"
import { ActionButton } from "@/components/ai/action-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Play,
  RefreshCw,
  RotateCw,
  Scale,
  Trash2,
  FileText,
  Zap,
  AlertTriangle
} from "lucide-react"

export default function ActionsPage() {
  const retryFailed = useRetryFailed()
  const runOrchestrator = useRunOrchestrator()
  const runScheduler = useRunScheduler()
  const rebalanceQueue = useRebalanceQueue()
  const clearFailed = useClearFailed()
  const generateReport = useGenerateReport()

  const handleAction = async (
    action: () => Promise<any>,
    successMessage: string
  ) => {
    try {
      await action()
      alert(successMessage)
    } catch (error) {
      alert(`Failed: ${error instanceof Error ? error.message : "Unknown error"}`)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          Manual Actions
        </h1>
        <p className="text-muted-foreground mt-2">
          Execute system operations directly
        </p>
      </div>

      {/* Critical Actions */}
      <Card className="border-red-200">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <CardTitle className="text-red-700">Critical Actions</CardTitle>
          </div>
          <CardDescription>Use with caution - affects live system</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <ActionButton
              label="Run Orchestrator Tick"
              onClick={() => handleAction(
                () => runOrchestrator.mutateAsync(),
                "Orchestrator tick completed successfully!"
              )}
              isLoading={runOrchestrator.isPending}
              icon={<Zap className="h-4 w-4" />}
              variant="destructive"
            />
            <ActionButton
              label="Run Scheduler Tick"
              onClick={() => handleAction(
                () => runScheduler.mutateAsync(false),
                "Scheduler tick completed successfully!"
              )}
              isLoading={runScheduler.isPending}
              icon={<Play className="h-4 w-4" />}
              variant="destructive"
            />
          </div>
        </CardContent>
      </Card>

      {/* Queue Management */}
      <Card>
        <CardHeader>
          <CardTitle>Queue Management</CardTitle>
          <CardDescription>Manage the publishing queue</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <ActionButton
              label="Rebalance Queue"
              onClick={() => handleAction(
                () => rebalanceQueue.mutateAsync(),
                "Queue rebalanced successfully!"
              )}
              isLoading={rebalanceQueue.isPending}
              icon={<Scale className="h-4 w-4" />}
            />
            <ActionButton
              label="Retry Failed Publications"
              onClick={() => handleAction(
                () => retryFailed.mutateAsync(),
                "Failed publications queued for retry!"
              )}
              isLoading={retryFailed.isPending}
              icon={<RefreshCw className="h-4 w-4" />}
            />
            <ActionButton
              label="Clear Old Failed Items"
              onClick={() => handleAction(
                () => clearFailed.mutateAsync(7),
                "Old failed items cleared!"
              )}
              isLoading={clearFailed.isPending}
              icon={<Trash2 className="h-4 w-4" />}
              variant="outline"
            />
          </div>
        </CardContent>
      </Card>

      {/* System Operations */}
      <Card>
        <CardHeader>
          <CardTitle>System Operations</CardTitle>
          <CardDescription>General system utilities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <ActionButton
              label="Generate System Report"
              onClick={() => handleAction(
                async () => {
                  const result = await generateReport.mutateAsync()
                  console.log("Report:", result)
                  return result
                },
                "System report generated! Check console for details."
              )}
              isLoading={generateReport.isPending}
              icon={<FileText className="h-4 w-4" />}
              variant="secondary"
            />
            <ActionButton
              label="Run Scheduler (Dry Run)"
              onClick={() => handleAction(
                () => runScheduler.mutateAsync(true),
                "Dry run completed! No changes made."
              )}
              isLoading={runScheduler.isPending}
              icon={<RotateCw className="h-4 w-4" />}
              variant="outline"
            />
          </div>
        </CardContent>
      </Card>

      {/* Action Guidelines */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-blue-700">Action Guidelines</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-900 space-y-2">
          <p>
            <strong>Orchestrator Tick:</strong> Manually triggers the orchestrator decision engine. 
            Use when system is saturated or to process pending decisions immediately.
          </p>
          <p>
            <strong>Scheduler Tick:</strong> Processes pending clips and schedules publications. 
            Use dry run mode to preview changes without applying them.
          </p>
          <p>
            <strong>Rebalance Queue:</strong> Optimizes scheduled publication times to avoid conflicts 
            and distribute load evenly across time slots.
          </p>
          <p>
            <strong>Retry Failed:</strong> Resets failed publications to pending status, giving them 
            another chance to publish successfully.
          </p>
          <p>
            <strong>Clear Old Failed:</strong> Removes failed publication records older than 7 days 
            to maintain database cleanliness.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
