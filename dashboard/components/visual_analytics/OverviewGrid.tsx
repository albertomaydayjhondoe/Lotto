/**
 * OverviewGrid Component (PASO 8.4)
 * 
 * Grid layout for overview statistics
 */

'use client';

import { StatCard } from './StatCard';
import type { AnalyticsOverview } from '@/lib/visual_analytics/types';
import {
  BarChart3,
  Briefcase,
  Send,
  Target,
  TrendingUp,
  Clock,
  Award,
} from 'lucide-react';

export interface OverviewGridProps {
  data: AnalyticsOverview;
}

export function OverviewGrid({ data }: OverviewGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Total Clips"
        value={data.total_clips.toLocaleString()}
        subtitle={`${data.clips_per_day.toFixed(1)} per day`}
        icon={BarChart3}
        color="blue"
      />
      <StatCard
        title="Total Jobs"
        value={data.total_jobs.toLocaleString()}
        subtitle={`${(data.avg_job_duration_ms / 1000).toFixed(1)}s avg duration`}
        icon={Briefcase}
        color="green"
      />
      <StatCard
        title="Publications"
        value={data.total_publications.toLocaleString()}
        subtitle={`${data.publication_success_rate.toFixed(1)}% success rate`}
        icon={Send}
        color="purple"
      />
      <StatCard
        title="Campaigns"
        value={data.total_campaigns.toLocaleString()}
        subtitle="Active campaigns"
        icon={Target}
        color="yellow"
      />
      
      <StatCard
        title="Weekly Rate"
        value={data.clips_per_week.toFixed(0)}
        subtitle="Clips per week"
        icon={TrendingUp}
        color="blue"
      />
      <StatCard
        title="Monthly Rate"
        value={data.clips_per_month.toFixed(0)}
        subtitle="Clips per month"
        icon={Clock}
        color="green"
      />
      <StatCard
        title="Avg Clip Score"
        value={data.avg_clip_score.toFixed(2)}
        subtitle="Visual quality score"
        icon={Award}
        color="purple"
      />
      <StatCard
        title="Top Clips"
        value={data.top_videos_by_score.length}
        subtitle="High performers"
        icon={BarChart3}
        color="yellow"
      />
    </div>
  );
}
