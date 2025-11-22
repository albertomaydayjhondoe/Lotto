"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader } from "@/components/ui/loader"
import { ChartContainer } from "@/components/ui/chart-container"
import { useDashboardOverview } from "@/hooks/use-dashboard-overview"
import { 
  Video, 
  Scissors, 
  Send, 
  Clock, 
  Activity, 
  Target 
} from "lucide-react"
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

export default function DashboardPage() {
  const { data, isLoading, error } = useDashboardOverview()

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
        Error loading dashboard data. Make sure the backend is running.
      </div>
    )
  }

  if (!data) return null

  // Prepare chart data
  const publicationStatusData = [
    { name: "Success", value: data.total_publications - data.failed_publications - data.pending_publications },
    { name: "Pending", value: data.pending_publications },
    { name: "Failed", value: data.failed_publications },
  ]

  const queueData = [
    { name: "Pending", count: data.pending_publications },
    { name: "Processing", count: data.active_jobs },
    { name: "Completed", count: data.total_publications - data.pending_publications },
  ]

  const activityData = [
    { day: "Mon", actions: 45 },
    { day: "Tue", actions: 52 },
    { day: "Wed", actions: 38 },
    { day: "Thu", actions: 65 },
    { day: "Fri", actions: 48 },
    { day: "Sat", actions: 30 },
    { day: "Sun", actions: 25 },
  ]

  const COLORS = ["#10b981", "#3b82f6", "#ef4444"]

  const stats = [
    {
      title: "Total Videos",
      value: data.total_videos,
      icon: Video,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
    },
    {
      title: "Total Clips",
      value: data.total_clips,
      icon: Scissors,
      color: "text-purple-600",
      bgColor: "bg-purple-100",
    },
    {
      title: "Total Publications",
      value: data.total_publications,
      icon: Send,
      color: "text-green-600",
      bgColor: "bg-green-100",
    },
    {
      title: "Pending Publications",
      value: data.pending_publications,
      icon: Clock,
      color: "text-yellow-600",
      bgColor: "bg-yellow-100",
    },
    {
      title: "Active Jobs",
      value: data.active_jobs,
      icon: Activity,
      color: "text-red-600",
      bgColor: "bg-red-100",
    },
    {
      title: "Active Campaigns",
      value: data.active_campaigns,
      icon: Target,
      color: "text-indigo-600",
      bgColor: "bg-indigo-100",
    },
  ]

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <div className={`${stat.bgColor} p-2 rounded-lg`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              {stat.title === "Total Publications" && (
                <p className="text-xs text-muted-foreground mt-1">
                  {data.success_rate.toFixed(1)}% success rate
                </p>
              )}
              {stat.title === "Total Clips" && data.avg_visual_score > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  Avg score: {data.avg_visual_score.toFixed(2)}
                </p>
              )}
              {stat.title === "Pending Publications" && data.avg_processing_time_ms > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  Avg: {(data.avg_processing_time_ms / 1000).toFixed(1)}s
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Publication Status Pie Chart */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Publications by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={publicationStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {publicationStatusData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Queue Bar Chart */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Publication Queue</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={queueData}>
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

        {/* Activity Line Chart */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Weekly Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={activityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="actions"
                    stroke="#10b981"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
