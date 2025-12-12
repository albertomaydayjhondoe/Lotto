"use client"

/**
 * AI Overview Page
 * 
 * System analysis with health metrics and detected issues.
 */

import { useSystemAnalysis } from "@/lib/ai/hooks"
import { HealthCard } from "@/components/ai/health-card"
import { IssuesList } from "@/components/ai/issues-list"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader } from "@/components/ui/loader"
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { Activity, TrendingUp, AlertTriangle } from "lucide-react"

export default function AIOverviewPage() {
  const { data: analysis, isLoading, error } = useSystemAnalysis()

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
            <CardTitle className="text-red-700">Error Loading Analysis</CardTitle>
            <CardDescription className="text-red-600">
              {error instanceof Error ? error.message : "Failed to load system analysis"}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (!analysis) {
    return null
  }

  // Prepare chart data
  const platformData = Object.entries(analysis.metrics.platform_distribution).map(([platform, count]) => ({
    name: platform.charAt(0).toUpperCase() + platform.slice(1),
    value: count
  }))

  const COLORS = ["#8b5cf6", "#ec4899", "#f59e0b", "#3b82f6"]

  const metricsData = [
    {
      name: "Clips Ready",
      value: analysis.metrics.total_clips_ready
    },
    {
      name: "In Queue",
      value: analysis.metrics.total_in_queue
    },
    {
      name: "Pending",
      value: analysis.pending_scheduled
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          AI System Analysis
        </h1>
        <p className="text-muted-foreground mt-2">
          Real-time intelligent analysis of system health and performance
        </p>
      </div>

      {/* Health Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <HealthCard
          title="Queue Health"
          status={analysis.queue_health}
          metric={`${analysis.pending_scheduled} pending`}
          description="Publishing queue status"
        />
        <HealthCard
          title="Orchestrator"
          status={analysis.orchestrator_health}
          description="Decision engine health"
        />
        <HealthCard
          title="Campaigns"
          status={analysis.campaigns_status}
          description="Campaign processing status"
        />
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <div className="bg-blue-50 p-2 rounded-lg">
              <TrendingUp className="h-4 w-4 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(analysis.publish_success_rate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Publication success rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Platform Distribution</CardTitle>
            <CardDescription>Posts per platform</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={platformData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {platformData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Metrics</CardTitle>
            <CardDescription>Current system load</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Clips Ready</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{analysis.metrics.total_clips_ready}</div>
            <p className="text-xs text-muted-foreground mt-1">Ready for publication</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Processing Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {analysis.metrics.avg_processing_time_ms 
                ? `${(analysis.metrics.avg_processing_time_ms / 1000).toFixed(1)}s`
                : "N/A"
              }
            </div>
            <p className="text-xs text-muted-foreground mt-1">Average publication time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(analysis.metrics.failed_rate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">Failed publications rate</p>
          </CardContent>
        </Card>
      </div>

      {/* Best Clips Per Platform */}
      {Object.keys(analysis.best_clip_per_platform).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Best Clips by Platform</CardTitle>
            <CardDescription>Highest scoring clips ready for publication</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              {Object.entries(analysis.best_clip_per_platform).map(([platform, clip]) => (
                <div key={platform} className="p-4 border rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">{platform}</span>
                    <span className="text-2xl font-bold text-purple-600">
                      {(clip.score * 100).toFixed(0)}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p>Duration: {clip.duration}s</p>
                    <p className="truncate">ID: {clip.clip_id.slice(0, 8)}...</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Issues List */}
      <IssuesList issues={analysis.issues_detected} />
    </div>
  )
}
