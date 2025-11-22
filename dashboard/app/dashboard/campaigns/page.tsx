"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Loader } from "@/components/ui/loader"
import { PlatformIcon } from "@/components/ui/platform-icon"
import { StatusDot } from "@/components/ui/status-dot"
import { useDashboardCampaigns } from "@/hooks/use-dashboard-campaigns"
import { Target, Sparkles, Send, Archive } from "lucide-react"

// Mock campaigns
const mockCampaigns = [
  {
    id: 1,
    name: "Summer Product Launch",
    status: "scheduled" as const,
    clips: {
      instagram: 5,
      tiktok: 3,
      youtube: 2,
      facebook: 4,
    },
    total_clips: 14,
    scheduled_date: "2025-11-25",
  },
  {
    id: 2,
    name: "Holiday Special Campaign",
    status: "draft" as const,
    clips: {
      instagram: 8,
      tiktok: 6,
      youtube: 3,
      facebook: 5,
    },
    total_clips: 22,
    scheduled_date: null,
  },
  {
    id: 3,
    name: "Brand Awareness Q4",
    status: "published" as const,
    clips: {
      instagram: 12,
      tiktok: 8,
      youtube: 5,
      facebook: 10,
    },
    total_clips: 35,
    scheduled_date: "2025-11-20",
  },
]

export default function CampaignsPage() {
  const { data, isLoading, error } = useDashboardCampaigns()

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
        Error loading campaigns data
      </div>
    )
  }

  const handleViewRecommendations = (campaignId: number) => {
    alert(`View Rule Engine recommendations for campaign #${campaignId}`)
  }

  const handlePublishCampaign = (campaignId: number) => {
    alert(`Publish campaign #${campaignId}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Campaigns</h2>
        <Button>
          <Target className="h-4 w-4 mr-2" />
          New Campaign
        </Button>
      </div>

      {/* Campaign Stats */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Draft</CardTitle>
            <StatusDot status="draft" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.draft || 0}</div>
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
            <CardTitle className="text-sm font-medium">Published</CardTitle>
            <StatusDot status="published" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.published || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Archived</CardTitle>
            <Archive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.archived || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Active Campaigns */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">Active Campaigns</h3>
        {mockCampaigns.map((campaign) => (
          <Card key={campaign.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                    <Target className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{campaign.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {campaign.total_clips} clips selected
                    </p>
                  </div>
                </div>
                <Badge
                  variant={
                    campaign.status === "published"
                      ? "success"
                      : campaign.status === "scheduled"
                      ? "pending"
                      : "secondary"
                  }
                >
                  <StatusDot status={campaign.status} className="mr-2" />
                  {campaign.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Platform Breakdown */}
                <div>
                  <p className="text-sm font-medium mb-2">Clips by Platform</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(campaign.clips).map(([platform, count]) => (
                      <div
                        key={platform}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center space-x-2">
                          <PlatformIcon
                            platform={platform as "instagram" | "tiktok" | "youtube" | "facebook"}
                            className="h-4 w-4"
                          />
                          <span className="text-sm capitalize">{platform}</span>
                        </div>
                        <span className="text-sm font-semibold">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Campaign Info */}
                {campaign.scheduled_date && (
                  <div className="text-sm text-muted-foreground">
                    Scheduled for: <span className="font-medium">{campaign.scheduled_date}</span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-3 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewRecommendations(campaign.id)}
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    View Recommendations
                  </Button>
                  {campaign.status === "draft" && (
                    <Button
                      size="sm"
                      onClick={() => handlePublishCampaign(campaign.id)}
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Publish Campaign
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
