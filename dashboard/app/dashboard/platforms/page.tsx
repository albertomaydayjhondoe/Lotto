"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader } from "@/components/ui/loader"
import { ChartContainer } from "@/components/ui/chart-container"
import { PlatformIcon } from "@/components/ui/platform-icon"
import { Badge } from "@/components/ui/badge"
import { useDashboardPlatforms } from "@/hooks/use-dashboard-platforms"
import { TrendingUp, TrendingDown, AlertCircle } from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

export default function PlatformsPage() {
  const { data, isLoading, error } = useDashboardPlatforms()

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
        Error loading platforms data
      </div>
    )
  }

  if (!data) return null

  const platforms = [
    { key: "instagram", name: "Instagram", data: data.instagram },
    { key: "tiktok", name: "TikTok", data: data.tiktok },
    { key: "youtube", name: "YouTube", data: data.youtube },
    { key: "facebook", name: "Facebook", data: data.facebook },
  ]

  // Comparison chart data
  const comparisonData = platforms.map(p => ({
    name: p.name,
    published: p.data.posts_published,
    pending: p.data.posts_pending,
    successRate: p.data.success_rate * 100,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Platform Performance</h2>
      </div>

      {/* Platform Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {platforms.map((platform) => (
          <Card key={platform.key} className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-bl-full" />
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <PlatformIcon 
                    platform={platform.key as "instagram" | "tiktok" | "youtube" | "facebook"} 
                    className="h-6 w-6"
                  />
                  <CardTitle>{platform.name}</CardTitle>
                </div>
                {platform.data.success_rate >= 0.8 ? (
                  <TrendingUp className="h-5 w-5 text-green-500" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-500" />
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Posts Today</span>
                  <span className="text-sm font-semibold">
                    {platform.data.posts_published}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Pending</span>
                  <span className="text-sm font-semibold text-yellow-600">
                    {platform.data.posts_pending}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Success Rate</span>
                  <Badge
                    variant={
                      platform.data.success_rate >= 0.8
                        ? "success"
                        : platform.data.success_rate >= 0.5
                        ? "warning"
                        : "destructive"
                    }
                  >
                    {(platform.data.success_rate * 100).toFixed(1)}%
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Avg Score</span>
                  <span className="text-sm font-semibold">
                    {platform.data.avg_visual_score.toFixed(2)}
                  </span>
                </div>
              </div>

              {platform.data.success_rate < 0.5 && (
                <div className="flex items-start space-x-2 p-3 bg-red-50 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-red-500 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-red-700">Last Failure</p>
                    <p className="text-xs text-red-600">API rate limit exceeded</p>
                  </div>
                </div>
              )}

              <div className="pt-2">
                <div className="text-xs text-muted-foreground mb-1">Clips Ready</div>
                <div className="text-2xl font-bold">{platform.data.clips_ready}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Performance Comparison Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Publications Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="published" fill="#10b981" name="Published" />
                  <Bar dataKey="pending" fill="#f59e0b" name="Pending" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Success Rate Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Bar dataKey="successRate" fill="#8b5cf6" name="Success Rate %" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Platform Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Total Posts</p>
              <p className="text-3xl font-bold">
                {platforms.reduce((sum, p) => sum + p.data.posts_published, 0)}
              </p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Total Pending</p>
              <p className="text-3xl font-bold">
                {platforms.reduce((sum, p) => sum + p.data.posts_pending, 0)}
              </p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Avg Success Rate</p>
              <p className="text-3xl font-bold">
                {(
                  platforms.reduce((sum, p) => sum + p.data.success_rate, 0) /
                  platforms.length *
                  100
                ).toFixed(0)}
                %
              </p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Total Clips Ready</p>
              <p className="text-3xl font-bold">
                {platforms.reduce((sum, p) => sum + p.data.clips_ready, 0)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
