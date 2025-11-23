/**
 * Visual Analytics Overview Page (PASO 8.4)
 * 
 * Main analytics dashboard showing comprehensive overview
 */

'use client';

import { useState } from 'react';
import { useOverviewAnalytics } from '@/lib/visual_analytics/hooks';
import {
  OverviewGrid,
  ChartCard,
  ClipRankingsTable,
  DateRangeFilter,
  LoadingState,
  ErrorState,
  EmptyState,
  LineChartWidget,
} from '@/components/visual_analytics';

export default function VisualAnalyticsOverviewPage() {
  const [daysBack, setDaysBack] = useState(30);
  const { data, isLoading, isError, error, refetch } = useOverviewAnalytics({ days_back: daysBack });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <LoadingState message="Loading analytics overview..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8">
        <ErrorState
          message={error?.message || 'Failed to load analytics'}
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

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Overview</h1>
          <p className="text-muted-foreground mt-1">
            Comprehensive view of your content performance
          </p>
        </div>
        <DateRangeFilter value={daysBack} onChange={setDaysBack} />
      </div>

      {/* Overview Grid */}
      <OverviewGrid data={data} />

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Correlations"
          description="Relationship between metrics"
        >
          {data.correlations && data.correlations.length > 0 ? (
            <div className="space-y-4">
              {data.correlations.map((corr, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      {corr.metric_x} → {corr.metric_y}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      n = {corr.sample_size}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-32 rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${corr.correlation * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium w-12 text-right">
                      {corr.correlation.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No correlation data available
            </p>
          )}
        </ChartCard>

        <ChartCard
          title="Rule Engine Performance"
          description="Rule evaluation metrics"
        >
          <div className="space-y-4">
            {Object.entries(data.rule_engine_metrics).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <p className="text-sm font-medium capitalize">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="text-lg font-bold">{String(value)}</p>
              </div>
            ))}
            {Object.keys(data.rule_engine_metrics).length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No rule engine metrics available
              </p>
            )}
          </div>
        </ChartCard>
      </div>

      {/* Top Performers */}
      <ClipRankingsTable clips={data.top_videos_by_score} />

      {/* Date Range Info */}
      <div className="text-xs text-muted-foreground text-center">
        Data from {new Date(data.date_range.start).toLocaleDateString()} to{' '}
        {new Date(data.date_range.end).toLocaleDateString()} · Generated at{' '}
        {new Date(data.generated_at).toLocaleString()}
      </div>
    </div>
  );
}
