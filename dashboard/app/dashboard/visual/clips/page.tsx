/**
 * Visual Analytics Clips Page (PASO 8.4)
 * 
 * Clips distribution and performance analysis
 */

'use client';

import { useState } from 'react';
import { useClipsAnalytics } from '@/lib/visual_analytics/hooks';
import {
  ClipRankingsTable,
  ChartCard,
  BarChartWidget,
  DateRangeFilter,
  LoadingState,
  ErrorState,
  EmptyState,
} from '@/components/visual_analytics';

export default function VisualAnalyticsClipsPage() {
  const [daysBack, setDaysBack] = useState(30);
  const { data, isLoading, isError, error, refetch } = useClipsAnalytics({ days_back: daysBack });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <LoadingState message="Loading clips analytics..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8">
        <ErrorState
          message={error?.message || 'Failed to load clips analytics'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (!data || data.total_clips === 0) {
    return (
      <div className="container mx-auto py-8">
        <EmptyState title="No clips data" message="No clips found for the selected time period" />
      </div>
    );
  }

  // Prepare histogram data for charts
  const durationChartData = data.by_duration.bins.map((bin, index) => ({
    name: `${Math.round(bin / 1000)}s`,
    value: data.by_duration.counts[index] || 0,
  }));

  const scoreChartData = data.by_score.bins.map((bin, index) => ({
    name: bin.toFixed(2),
    value: data.by_score.counts[index] || 0,
  }));

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Clips Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Distribution and performance of generated clips
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
          <p className="text-sm text-muted-foreground">Avg Score</p>
          <p className="mt-2 text-3xl font-bold">{data.avg_score.toFixed(2)}</p>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <p className="text-sm text-muted-foreground">Avg Duration</p>
          <p className="mt-2 text-3xl font-bold">
            {Math.round(data.avg_duration / 1000)}s
          </p>
        </div>
      </div>

      {/* Distribution Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Duration Distribution"
          description="Histogram of clip durations"
        >
          {durationChartData.length > 0 ? (
            <BarChartWidget data={durationChartData} color="#3b82f6" />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No duration data available
            </p>
          )}
        </ChartCard>

        <ChartCard
          title="Score Distribution"
          description="Histogram of visual quality scores"
        >
          {scoreChartData.length > 0 ? (
            <BarChartWidget data={scoreChartData} color="#10b981" />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No score data available
            </p>
          )}
        </ChartCard>
      </div>

      {/* Top Clips */}
      <ClipRankingsTable
        clips={data.top_clips}
        title="Top Performing Clips"
        description="Clips with highest visual quality scores"
      />
    </div>
  );
}
