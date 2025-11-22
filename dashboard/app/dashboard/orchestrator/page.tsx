"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader } from "@/components/ui/loader"
import { ChartContainer } from "@/components/ui/chart-container"
import { DateTimeDisplay } from "@/components/ui/datetime-display"
import { useDashboardOrchestrator } from "@/hooks/use-dashboard-orchestrator"
import { Activity, CheckCircle, XCircle, Clock, TrendingUp } from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

// Mock data
const mockDecisions = [
  { id: 1, action: "schedule_publication", platform: "instagram", timestamp: new Date(Date.now() - 300000), result: "success" },
  { id: 2, action: "optimize_clip", clip_id: "clip_123", timestamp: new Date(Date.now() - 600000), result: "success" },
  { id: 3, action: "retry_failed", platform: "tiktok", timestamp: new Date(Date.now() - 900000), result: "failed" },
  { id: 4, action: "schedule_publication", platform: "youtube", timestamp: new Date(Date.now() - 1200000), result: "success" },
  { id: 5, action: "validate_rules", campaign_id: "camp_456", timestamp: new Date(Date.now() - 1500000), result: "success" },
]

const mockEvents = [
  { id: 1, type: "publication_scheduled", details: "Instagram post scheduled", timestamp: new Date(Date.now() - 240000) },
  { id: 2, type: "job_completed", details: "Video processing completed", timestamp: new Date(Date.now() - 480000) },
  { id: 3, type: "orchestration_started", details: "Campaign orchestration initiated", timestamp: new Date(Date.now() - 720000) },
  { id: 4, type: "rule_applied", details: "Platform rules validated", timestamp: new Date(Date.now() - 960000) },
  { id: 5, type: "publication_completed", details: "TikTok post published successfully", timestamp: new Date(Date.now() - 1200000) },
]

export default function OrchestratorPage() {
  const { data, isLoading, error } = useDashboardOrchestrator()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 p-8">
        Error loading orchestrator data
      </div>
    )
  }

  const actionTypeData = [
    { name: "Schedule", count: 45 },
    { name: "Optimize", count: 32 },
    { name: "Retry", count: 12 },
    { name: "Validate", count: 28 },
  ]

  const orchestratorStatus = data?.saturation_rate < 0.7 ? "healthy" : data?.saturation_rate < 0.9 ? "warning" : "critical"

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Orchestrator</h2>
        <Badge
          variant={orchestratorStatus === "healthy" ? "success" : orchestratorStatus === "warning" ? "warning" : "destructive"}
        >
          {orchestratorStatus === "healthy" ? "● Online" : orchestratorStatus === "warning" ? "● Warning" : "● Critical"}
        </Badge>
      </div>

      {/* Orchestrator Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total_jobs || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.pending_jobs || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
            <TrendingUp className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.processing_jobs || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Saturation</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {((data?.saturation_rate || 0) * 100).toFixed(0)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {data?.completed_jobs || 0} completed
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Actions Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Actions by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={actionTypeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Recent Decisions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Decisions (Last 20)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockDecisions.slice(0, 5).map((decision) => (
                <div
                  key={decision.id}
                  className="flex items-start justify-between border-b pb-2 last:border-0"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium">{decision.action}</p>
                    <p className="text-xs text-muted-foreground">
                      {decision.platform || decision.clip_id || decision.campaign_id}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {decision.result === "success" ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="text-xs text-muted-foreground">
                      <DateTimeDisplay date={decision.timestamp} formatString="HH:mm" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Events */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Events (Last 20)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {mockEvents.map((event) => (
              <div
                key={event.id}
                className="flex items-center justify-between border-b pb-3 last:border-0"
              >
                <div className="flex-1">
                  <Badge variant="outline" className="mb-1">
                    {event.type}
                  </Badge>
                  <p className="text-sm text-muted-foreground">{event.details}</p>
                </div>
                <DateTimeDisplay
                  date={event.timestamp}
                  formatString="MMM dd, HH:mm"
                  className="text-xs text-muted-foreground"
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
