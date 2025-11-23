/**
 * Visual Analytics Campaigns Page (PASO 8.4)
 * 
 * Campaign performance breakdown and metrics
 */

'use client';

import { useState } from 'react';
import { useCampaignAnalytics } from '@/lib/visual_analytics/hooks';
import {
  ChartCard,
  BarChartWidget,
  DateRangeFilter,
  LoadingState,
  ErrorState,
  EmptyState,
} from '@/components/visual_analytics';
import { format } from 'date-fns';

export default function VisualAnalyticsCampaignsPage() {
  const [daysBack, setDaysBack] = useState(30);
  const { data, isLoading, isError, error, refetch } = useCampaignAnalytics({ days_back: daysBack });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <LoadingState message="Loading campaign analytics..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8">
        <ErrorState
          message={error?.message || 'Failed to load campaign analytics'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (!data || data.total_campaigns === 0) {
    return (
      <div className="container mx-auto py-8">
        <EmptyState
          title="No campaigns data"
          message="No campaigns found for the selected time period"
        />
      </div>
    );
  }

  const clipsChartData = data.campaigns.map(c => ({
    name: c.name.length > 20 ? c.name.slice(0, 20) + '...' : c.name,
    value: c.clips_count,
  }));

  const pubsChartData = data.campaigns.map(c => ({
    name: c.name.length > 20 ? c.name.slice(0, 20) + '...' : c.name,
    value: c.publications_count,
  }));

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Campaign Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Performance metrics for ad campaigns
          </p>
        </div>
        <DateRangeFilter value={daysBack} onChange={setDaysBack} />
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border bg-card p-6">
          <p className="text-sm text-muted-foreground">Total Campaigns</p>
          <p className="mt-2 text-3xl font-bold">{data.total_campaigns}</p>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <p className="text-sm text-muted-foreground">Active Campaigns</p>
          <p className="mt-2 text-3xl font-bold">{data.active_campaigns}</p>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <p className="text-sm text-muted-foreground">Avg Clips per Campaign</p>
          <p className="mt-2 text-3xl font-bold">
            {data.avg_clips_per_campaign.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Campaign Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Clips by Campaign"
          description="Number of clips per campaign"
        >
          {clipsChartData.length > 0 ? (
            <BarChartWidget data={clipsChartData} color="#3b82f6" />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No clips data available
            </p>
          )}
        </ChartCard>

        <ChartCard
          title="Publications by Campaign"
          description="Number of publications per campaign"
        >
          {pubsChartData.length > 0 ? (
            <BarChartWidget data={pubsChartData} color="#10b981" />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No publications data available
            </p>
          )}
        </ChartCard>
      </div>

      {/* Campaign Table */}
      <ChartCard
        title="All Campaigns"
        description="Complete list of campaigns"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-muted-foreground">
                <th className="pb-3 pr-4 font-medium">Name</th>
                <th className="pb-3 pr-4 font-medium">Status</th>
                <th className="pb-3 pr-4 font-medium text-right">Clips</th>
                <th className="pb-3 pr-4 font-medium text-right">Publications</th>
                <th className="pb-3 pr-4 font-medium text-right">Avg Score</th>
                <th className="pb-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {data.campaigns.map((campaign) => (
                <tr key={campaign.campaign_id} className="border-b last:border-0">
                  <td className="py-3 pr-4">
                    <p className="font-medium">{campaign.name}</p>
                    <p className="text-xs text-muted-foreground font-mono">
                      {campaign.campaign_id.slice(0, 8)}...
                    </p>
                  </td>
                  <td className="py-3 pr-4">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                        campaign.status === 'active'
                          ? 'bg-green-500/10 text-green-600'
                          : 'bg-gray-500/10 text-gray-600'
                      }`}
                    >
                      {campaign.status}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right">{campaign.clips_count}</td>
                  <td className="py-3 pr-4 text-right">{campaign.publications_count}</td>
                  <td className="py-3 pr-4 text-right">
                    {campaign.avg_clip_score.toFixed(2)}
                  </td>
                  <td className="py-3 text-sm text-muted-foreground">
                    {format(new Date(campaign.created_at), 'MMM dd, yyyy')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  );
}
