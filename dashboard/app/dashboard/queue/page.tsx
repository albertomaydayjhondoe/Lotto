"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Loader } from "@/components/ui/loader"
import { StatusDot } from "@/components/ui/status-dot"
import { PlatformIcon } from "@/components/ui/platform-icon"
import { DateTimeDisplay } from "@/components/ui/datetime-display"
import { useDashboardQueue } from "@/hooks/use-dashboard-queue"
import { Play, RotateCcw, Eye, Clock } from "lucide-react"

// Mock queue items for demo
const mockQueueItems = [
  {
    id: 1,
    clip_id: "clip_abc123",
    platform: "instagram" as const,
    status: "pending" as const,
    scheduled_for: new Date(Date.now() + 3600000).toISOString(),
    requested_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: 2,
    clip_id: "clip_def456",
    platform: "tiktok" as const,
    status: "scheduled" as const,
    scheduled_for: new Date(Date.now() + 7200000).toISOString(),
    requested_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 3,
    clip_id: "clip_ghi789",
    platform: "youtube" as const,
    status: "processing" as const,
    scheduled_for: new Date(Date.now() + 1800000).toISOString(),
    requested_at: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 4,
    clip_id: "clip_jkl012",
    platform: "facebook" as const,
    status: "pending" as const,
    scheduled_for: new Date(Date.now() + 5400000).toISOString(),
    requested_at: new Date(Date.now() - 900000).toISOString(),
  },
]

export default function QueuePage() {
  const { data, isLoading, error } = useDashboardQueue()

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
        Error loading queue data
      </div>
    )
  }

  const handleForcePublish = (id: number) => {
    alert(`Force publish clip #${id}`)
  }

  const handleRetry = (id: number) => {
    alert(`Retry clip #${id}`)
  }

  const handleViewClip = (clipId: string) => {
    alert(`View clip: ${clipId}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Publication Queue</h2>
      </div>

      {/* Queue Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total in Queue</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total_in_queue || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <StatusDot status="pending" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.pending || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <StatusDot status="scheduled" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.scheduled || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
            <StatusDot status="processing" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.processing || 0}</div>
            {data?.avg_wait_time_ms && (
              <p className="text-xs text-muted-foreground mt-1">
                Avg wait: {(data.avg_wait_time_ms / 1000).toFixed(0)}s
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Queue Table */}
      <Card>
        <CardHeader>
          <CardTitle>Queue Items</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Clip ID</TableHead>
                <TableHead>Platform</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Scheduled For</TableHead>
                <TableHead>Requested At</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockQueueItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">#{item.id}</TableCell>
                  <TableCell>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {item.clip_id}
                    </code>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <PlatformIcon platform={item.platform} />
                      <span className="capitalize">{item.platform}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        item.status === "pending"
                          ? "pending"
                          : item.status === "processing"
                          ? "warning"
                          : "secondary"
                      }
                    >
                      <StatusDot status={item.status} className="mr-2" />
                      {item.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DateTimeDisplay date={item.scheduled_for} />
                  </TableCell>
                  <TableCell>
                    <DateTimeDisplay date={item.requested_at} />
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleForcePublish(item.id)}
                      >
                        <Play className="h-3 w-3 mr-1" />
                        Force
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRetry(item.id)}
                      >
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Retry
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleViewClip(item.clip_id)}
                      >
                        <Eye className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
