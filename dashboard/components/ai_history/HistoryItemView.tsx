/**
 * History Item View Component
 * 
 * Detailed view of a single AI reasoning run (PASO 8.2).
 */

"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { HistoryStatusBadge } from "./HistoryStatusBadge"
import { HistoryScoreCard } from "./HistoryScoreCard"
import type { AIHistoryItemDetail } from "@/lib/ai_history/types"
import { formatDistanceToNow } from "date-fns"

interface HistoryItemViewProps {
  item: AIHistoryItemDetail
  className?: string
}

export function HistoryItemView({ item, className }: HistoryItemViewProps) {
  return (
    <div className={className}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">AI Reasoning Run</h1>
            <p className="text-gray-500 mt-1">
              {new Date(item.created_at).toLocaleString()} •{" "}
              {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
            </p>
          </div>
          <HistoryStatusBadge status={item.status} />
        </div>
      </div>

      {/* Metadata Row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Triggered By</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xl font-semibold capitalize">{item.triggered_by}</span>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xl font-semibold">{item.duration_ms}ms</span>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xl font-semibold">{item.recommendations_count}</span>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Critical Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <span className={`text-xl font-semibold ${item.critical_issues_count > 0 ? 'text-red-600' : 'text-gray-400'}`}>
              {item.critical_issues_count}
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-6">
        {/* Left Column - Score Card */}
        <div>
          <HistoryScoreCard score={item.health_score} status={item.status} />
        </div>

        {/* Right Columns - Summary and Details */}
        <div className="col-span-2 space-y-6">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Health Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-2">Overall Health</p>
                <p className="text-lg capitalize">{item.summary.overall_health}</p>
              </div>
              
              {item.summary.key_insights.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">Key Insights</p>
                  <ul className="list-disc list-inside space-y-1">
                    {item.summary.key_insights.map((insight, idx) => (
                      <li key={idx} className="text-sm">{insight}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {item.summary.concerns.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">Concerns</p>
                  <ul className="list-disc list-inside space-y-1">
                    {item.summary.concerns.map((concern, idx) => (
                      <li key={idx} className="text-sm text-yellow-700">{concern}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {item.summary.positives.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">Positives</p>
                  <ul className="list-disc list-inside space-y-1">
                    {item.summary.positives.map((positive, idx) => (
                      <li key={idx} className="text-sm text-green-700">{positive}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              {item.recommendations.length === 0 ? (
                <p className="text-gray-500">No recommendations</p>
              ) : (
                <div className="space-y-3">
                  {item.recommendations.map((rec) => (
                    <div key={rec.id} className="border-l-4 border-blue-500 pl-4 py-2">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={rec.priority === "critical" ? "destructive" : "default"}>
                          {rec.priority}
                        </Badge>
                        <span className="text-xs text-gray-500">{rec.category}</span>
                      </div>
                      <h4 className="font-semibold">{rec.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                      <div className="flex gap-4 mt-2 text-xs text-gray-500">
                        <span>Impact: <span className="font-medium">{rec.impact}</span></span>
                        <span>Effort: <span className="font-medium">{rec.effort}</span></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Action Plan */}
          <Card>
            <CardHeader>
              <CardTitle>Action Plan</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Objective</p>
                  <p>{item.action_plan.objective}</p>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Duration</p>
                    <p className="text-sm">{item.action_plan.estimated_duration}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Risk Level</p>
                    <Badge variant={item.action_plan.risk_level === "high" ? "destructive" : "default"}>
                      {item.action_plan.risk_level}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Automated</p>
                    <p className="text-sm">{item.action_plan.automated ? "Yes" : "No"}</p>
                  </div>
                </div>
                
                {item.action_plan.steps.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-2">Steps</p>
                    <ol className="list-decimal list-inside space-y-2">
                      {item.action_plan.steps.map((step, idx) => (
                        <li key={idx} className="text-sm">
                          <span className="font-medium">{step.action}</span>
                          <span className="text-gray-500 ml-2">({step.duration})</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* System Snapshot */}
          <Card>
            <CardHeader>
              <CardTitle>System Snapshot</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Queue</p>
                  <p className="text-sm">Pending: {item.snapshot.queue_pending}</p>
                  <p className="text-sm">Processing: {item.snapshot.queue_processing}</p>
                  <p className="text-sm">Failed: {item.snapshot.queue_failed}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Clips</p>
                  <p className="text-sm">Ready: {item.snapshot.clips_ready}</p>
                  <p className="text-sm">Published: {item.snapshot.clips_published}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Jobs</p>
                  <p className="text-sm">Pending: {item.snapshot.jobs_pending}</p>
                  <p className="text-sm">Completed: {item.snapshot.jobs_completed}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Campaigns</p>
                  <p className="text-sm">Active: {item.snapshot.campaigns_active}</p>
                  <p className="text-sm">Paused: {item.snapshot.campaigns_paused}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Alerts</p>
                  <p className="text-sm text-red-600">Critical: {item.snapshot.alerts_critical}</p>
                  <p className="text-sm text-yellow-600">Warning: {item.snapshot.alerts_warning}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default HistoryItemView
