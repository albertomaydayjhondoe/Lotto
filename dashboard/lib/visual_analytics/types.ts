/**
 * TypeScript types for Visual Analytics (PASO 8.4)
 * 
 * Mirrors backend Pydantic schemas from backend/app/visual_analytics/schemas.py
 */

export interface TimeseriesPoint {
  timestamp: string;
  value: number;
}

export interface Timeseries {
  series_name: string;
  data: TimeseriesPoint[];
  color?: string;
}

export interface HeatmapCell {
  x: number; // Hour (0-23)
  y: number; // Day of week (0-6)
  value: number;
}

export interface HeatmapData {
  title: string;
  x_labels: string[]; // Hour labels
  y_labels: string[]; // Day labels
  cells: HeatmapCell[];
  color_scale: string;
}

export interface Distribution {
  bins: number[];
  counts: number[];
  label?: string;
}

export interface PlatformMetric {
  platform: string;
  clips_count: number;
  publications_count: number;
  avg_score: number;
  success_rate: number;
  total_views: number;
}

export interface PlatformStats {
  platforms: PlatformMetric[];
  total_clips: number;
  total_publications: number;
  best_platform: string | null;
}

export interface ClipRanking {
  clip_id: string;
  video_id: string;
  title: string | null;
  score: number;
  duration_ms: number;
}

export interface ClipsDistribution {
  by_duration: Distribution;
  by_score: Distribution;
  top_clips: ClipRanking[];
  total_clips: number;
  avg_score: number;
  avg_duration: number;
}

export interface CampaignMetric {
  campaign_id: string;
  name: string;
  status: string;
  clips_count: number;
  publications_count: number;
  avg_clip_score: number;
  created_at: string;
}

export interface CampaignBreakdown {
  campaigns: CampaignMetric[];
  total_campaigns: number;
  active_campaigns: number;
  avg_clips_per_campaign: number;
}

export interface TrendLine {
  metric_name: string;
  values: number[];
  timestamps: string[];
}

export interface TimelineData {
  jobs_timeline: Timeseries[];
  publications_timeline: Timeseries[];
  clips_timeline: Timeseries[];
  orchestrator_events: Timeseries[];
  date_range: {
    start: string;
    end: string;
  };
}

export interface CorrelationMetric {
  metric_x: string;
  metric_y: string;
  correlation: number;
  sample_size: number;
}

export interface AnalyticsOverview {
  // Counts
  total_clips: number;
  total_jobs: number;
  total_publications: number;
  total_campaigns: number;
  
  // Rates
  clips_per_day: number;
  clips_per_week: number;
  clips_per_month: number;
  
  // Averages
  avg_job_duration_ms: number;
  avg_clip_score: number;
  publication_success_rate: number;
  
  // Advanced analytics
  trends: TrendLine[];
  correlations: CorrelationMetric[];
  top_videos_by_score: ClipRanking[];
  rule_engine_metrics: Record<string, any>;
  
  // Metadata
  generated_at: string;
  date_range: {
    start: string;
    end: string;
  };
}

export interface AnalyticsSummary {
  total_clips: number;
  total_jobs: number;
  total_publications: number;
  avg_clip_score: number;
  generated_at: string;
}

// Query parameters types
export interface AnalyticsQueryParams {
  days_back?: number;
}

export interface HeatmapQueryParams extends AnalyticsQueryParams {
  metric?: 'clips' | 'jobs' | 'publications';
}

// API response wrapper
export interface ApiResponse<T> {
  data: T;
  error?: string;
}

// Chart data types (for recharts compatibility)
export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: any;
}

export interface LineChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color: string;
  }[];
}

export interface BarChartData {
  labels: string[];
  values: number[];
  colors?: string[];
}

export interface PieChartData {
  name: string;
  value: number;
  color?: string;
}
