/**
 * Visual Analytics Timeline Page (PASO 8.4)
 * 
 * Timeline view of system activity
 */

'use client';

import { useState } from 'react';
import { useTimelineAnalytics } from '@/lib/visual_analytics/hooks';
import {
  ChartCard,
  LineChartWidget,
  DateRangeFilter,
  LoadingState,
  ErrorState,
  EmptyState,
} from '@/components/visual_analytics';

export default function VisualAnalyticsTimelinePage() {
  const [daysBack, setDaysBack] = useState(7);
  const { data, isLoading, isError, error, refetch } = useTimelineAnalytics({ days_back: daysBack });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <LoadingState message="Loading timeline data..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8">
        <ErrorState
          message={error?.message || 'Failed to load timeline data'}
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

  const hasJobsData = data.jobs_timeline.some(s => s.data.length > 0);
  const hasPubsData = data.publications_timeline.some(s => s.data.length > 0);
  const hasClipsData = data.clips_timeline.some(s => s.data.length > 0);
  const hasOrchData = data.orchestrator_events.some(s => s.data.length > 0);

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Activity Timeline</h1>
          <p className="text-muted-foreground mt-1">
            Historical view of system activity over time
          </p>
        </div>
        <DateRangeFilter value={daysBack} onChange={setDaysBack} />
      </div>

      {/* Timeline Charts */}
      <div className="space-y-6">
        <ChartCard
          title="Jobs Activity"
          description="Job processing over time"
        >
          {hasJobsData ? (
            <LineChartWidget data={data.jobs_timeline} height={250} />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No jobs data for this time period
            </p>
          )}
        </ChartCard>

        <ChartCard
          title="Publications Activity"
          description="Content publishing over time"
        >
          {hasPubsData ? (
            <LineChartWidget data={data.publications_timeline} height={250} />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No publications data for this time period
            </p>
          )}
        </ChartCard>

        <ChartCard
          title="Clips Generation"
          description="Clip creation over time"
        >
          {hasClipsData ? (
            <LineChartWidget data={data.clips_timeline} height={250} />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No clips data for this time period
            </p>
          )}
        </ChartCard>

        <ChartCard
          title="Orchestrator Events"
          description="System orchestration events"
        >
          {hasOrchData ? (
            <LineChartWidget data={data.orchestrator_events} height={250} />
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No orchestrator events for this time period
            </p>
          )}
        </ChartCard>
      </div>

      {/* Date Range Info */}
      <div className="text-xs text-muted-foreground text-center">
        Showing data from {new Date(data.date_range.start).toLocaleDateString()} to{' '}
        {new Date(data.date_range.end).toLocaleDateString()}
      </div>
    </div>
  );
}
