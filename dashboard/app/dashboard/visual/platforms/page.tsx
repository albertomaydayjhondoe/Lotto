/**
 * Visual Analytics Platforms Page (PASO 8.4)
 * 
 * Platform performance breakdown and comparison
 */

'use client';

import { useState } from 'react';
import { usePlatformAnalytics } from '@/lib/visual_analytics/hooks';
import {
  PlatformsBreakdownCard,
  ChartCard,
  BarChartWidget,
  DateRangeFilter,
  LoadingState,
  ErrorState,
  EmptyState,
} from '@/components/visual_analytics';

export default function VisualAnalyticsPlatformsPage() {
  const [daysBack, setDaysBack] = useState(30);
  const { data, isLoading, isError, error, refetch } = usePlatformAnalytics({ days_back: daysBack });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <LoadingState message="Loading platform analytics..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8">
        <ErrorState
          message={error?.message || 'Failed to load platform analytics'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container mx-auto py-8">
        <EmptyState />
      </div>
    );
  }

  const clipsChartData = data.platforms.map(p => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    value: p.clips_count,
  }));

  const pubsChartData = data.platforms.map(p => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    value: p.publications_count,
  }));

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Platform Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Compare performance across social media platforms
          </p>
        </div>
        <DateRangeFilter value={daysBack} onChange={setDaysBack} />
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border bg-card p-6">
          <p className="text-sm text-muted-foreground">Total Clips</p>
          <p className="mt-2 text-3xl font-bold">{data.total_clips.toLocaleString()}</p>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <p className="text-sm text-muted-foreground">Total Publications</p>
          <p className="mt-2 text-3xl font-bold">{data.total_publications.toLocaleString()}</p>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <p className="text-sm text-muted-foreground">Best Platform</p>
          <p className="mt-2 text-3xl font-bold capitalize">
            {data.best_platform || 'N/A'}
          </p>
        </div>
      </div>

      {/* Platform Breakdown */}
      <PlatformsBreakdownCard data={data} />

      {/* Comparison Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Clips by Platform"
          description="Number of clips per platform"
        >
          <BarChartWidget data={clipsChartData} color="#3b82f6" />
        </ChartCard>

        <ChartCard
          title="Publications by Platform"
          description="Number of publications per platform"
        >
          <BarChartWidget data={pubsChartData} color="#10b981" />
        </ChartCard>
      </div>
    </div>
  );
}
