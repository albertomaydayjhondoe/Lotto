// dashboard/lib/meta_insights/api.ts

import { api } from '../api';

// Tipos TypeScript para Meta Insights
export interface InsightMetrics {
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
  ctr: number;
  cpc: number;
  roas: number;
  frequency: number;
  reach?: number;
  unique_clicks?: number;
  cost_per_conversion?: number;
}

export interface InsightResponse {
  id: string;
  entity_id: string;
  entity_type: string;
  date_start: string;
  date_end: string;
  metrics: InsightMetrics;
  created_at: string;
  updated_at: string;
}

export interface InsightTimeline {
  entity_id: string;
  entity_type: string;
  entity_name?: string;
  date_range: {
    start: string;
    end: string;
  };
  insights: InsightResponse[];
  total_insights: number;
  total_spend: number;
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
  total_revenue: number;
  avg_ctr: number;
  avg_cpc: number;
  avg_roas: number;
}

export interface InsightsOverviewResponse {
  timestamp: string;
  date_range: {
    start: string;
    end: string;
  };
  total_campaigns: number;
  active_campaigns: number;
  total_adsets: number;
  active_adsets: number;
  total_ads: number;
  active_ads: number;
  global_metrics: InsightMetrics;
  top_campaigns: Array<{
    id: string;
    name: string;
    avg_roas: number;
    total_spend: number;
  }>;
  top_adsets: Array<{
    id: string;
    name: string;
    avg_roas: number;
    total_spend: number;
  }>;
  top_ads: Array<{
    id: string;
    name: string;
    avg_roas: number;
    total_spend: number;
  }>;
  last_sync?: {
    timestamp: string;
    success: boolean;
    duration_seconds: number;
  };
  alerts: Array<{
    type: string;
    message: string;
    severity: string;
  }>;
}

export interface CampaignInsightsOverview {
  campaign_id: string;
  campaign_name: string;
  status: string;
  campaign_insights: InsightTimeline;
  adsets_count: number;
  adsets_active: number;
  adsets_paused: number;
  ads_count: number;
  ads_active: number;
  ads_paused: number;
  performance_summary: {
    roas: number;
    spend: number;
    revenue: number;
    efficiency_score: number;
  };
}

export interface AdsetInsightsOverview {
  adset_id: string;
  adset_name: string;
  campaign_id: string;
  campaign_name: string;
  status: string;
  adset_insights: InsightTimeline;
  ads_count: number;
  ads_active: number;
  ads_paused: number;
  targeting_summary?: {
    age_range: string;
    locations: string[];
    interests: string[];
  };
  budget_info?: {
    daily_budget: number;
    lifetime_budget?: number;
    bid_strategy: string;
  };
}

export interface AdInsightsOverview {
  ad_id: string;
  ad_name: string;
  adset_id: string;
  adset_name: string;
  campaign_id: string;
  campaign_name: string;
  status: string;
  ad_insights: InsightTimeline;
  creative_info?: {
    format: string;
    headline: string;
    description: string;
    call_to_action: string;
  };
  peer_comparison?: {
    adset_avg_roas: number;
    rank_in_adset: number;
    total_ads_in_adset: number;
    performance_percentile: number;
  };
}

export interface SyncReport {
  sync_id: string;
  sync_timestamp: string;
  sync_type: string;
  mode: string;
  date_range: {
    start: string;
    end: string;
  };
  days_back: number;
  campaigns: {
    processed: number;
    success: number;
    errors: number;
    skipped: number;
  };
  adsets: {
    processed: number;
    success: number;
    errors: number;
    skipped: number;
  };
  ads: {
    processed: number;
    success: number;
    errors: number;
    skipped: number;
  };
  total_duration_seconds: number;
  errors: string[];
  success: boolean;
  completion_percentage: number;
}

export interface ManualSyncRequest {
  days_back?: number;
  force?: boolean;
  entity_ids?: string[];
  entity_type?: string;
}

// Funciones de API para Meta Insights

/**
 * Obtiene una vista general de todos los insights
 */
export async function getInsightsOverview(days: number = 7): Promise<InsightsOverviewResponse> {
  const response = await api.get(`/meta/insights/overview?days=${days}`);
  return response.data;
}

/**
 * Obtiene insights detallados de una campaña
 */
export async function getCampaignInsights(
  campaignId: string, 
  days: number = 30
): Promise<CampaignInsightsOverview> {
  const response = await api.get(`/meta/insights/campaign/${campaignId}?days=${days}`);
  return response.data;
}

/**
 * Obtiene insights detallados de un adset
 */
export async function getAdsetInsights(
  adsetId: string, 
  days: number = 30
): Promise<AdsetInsightsOverview> {
  const response = await api.get(`/meta/insights/adset/${adsetId}?days=${days}`);
  return response.data;
}

/**
 * Obtiene insights detallados de un ad
 */
export async function getAdInsights(
  adId: string, 
  days: number = 30
): Promise<AdInsightsOverview> {
  const response = await api.get(`/meta/insights/ad/${adId}?days=${days}`);
  return response.data;
}

/**
 * Obtiene insights recientes de una entidad específica
 */
export async function getRecentInsights(
  entityId: string,
  entityType: 'campaign' | 'adset' | 'ad',
  days: number = 30
): Promise<InsightTimeline> {
  const response = await api.get(
    `/meta/insights/recent-insights/${entityId}?entity_type=${entityType}&days=${days}`
  );
  return response.data;
}

/**
 * Ejecuta una sincronización manual de insights
 */
export async function syncInsightsNow(request: ManualSyncRequest = {}): Promise<SyncReport> {
  const response = await api.post('/meta/insights/sync-now', request);
  return response.data;
}

/**
 * Obtiene resumen de insights (PASO 10.7)
 */
export async function getInsightsSummary(): Promise<{
  total_insights: number;
  latest_date: string | null;
  last_30_days: {
    spend: number;
    impressions: number;
    clicks: number;
    conversions: number;
    revenue: number;
    roas: number;
  };
}> {
  const response = await api.get('/meta/insights/summary');
  return response.data;
}

/**
 * Ejecuta sincronización completa (PASO 10.7)
 */
export async function runFullSync(daysBack: number = 7): Promise<{
  status: string;
  report: SyncReport;
}> {
  const response = await api.post(`/meta/insights/run?days_back=${daysBack}`);
  return response.data;
}

/**
 * Sincroniza insights de campaña específica (PASO 10.7)
 */
export async function syncCampaign(campaignId: string, daysBack: number = 7): Promise<{
  status: string;
  report: SyncReport;
}> {
  const response = await api.post(`/meta/insights/sync/campaign/${campaignId}?days_back=${daysBack}`);
  return response.data;
}

/**
 * Sincroniza insights de adset específico (PASO 10.7)
 */
export async function syncAdset(adsetId: string, daysBack: number = 7): Promise<{
  status: string;
  report: SyncReport;
}> {
  const response = await api.post(`/meta/insights/sync/adset/${adsetId}?days_back=${daysBack}`);
  return response.data;
}

/**
 * Sincroniza insights de ad específico (PASO 10.7)
 */
export async function syncAd(adId: string, daysBack: number = 7): Promise<{
  status: string;
  report: SyncReport;
}> {
  const response = await api.post(`/meta/insights/sync/ad/${adId}?days_back=${daysBack}`);
  return response.data;
}

/**
 * Obtiene información de la última sincronización (PASO 10.7)
 */
export async function getLastSyncInfo(): Promise<{
  last_sync_time: string | null;
  latest_insight_date: string | null;
  total_insights: number;
  scheduler_status: string;
}> {
  const response = await api.get('/meta/insights/last');
  return response.data;
}

/**
 * Funciones de utilidad para métricas
 */
export const InsightsUtils = {
  /**
   * Formatea un valor de spend como moneda USD
   */
  formatSpend: (spend: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(spend);
  },

  /**
   * Formatea un número con separadores de miles
   */
  formatNumber: (num: number): string => {
    return new Intl.NumberFormat('en-US').format(num);
  },

  /**
   * Formatea un porcentaje
   */
  formatPercentage: (value: number, decimals: number = 2): string => {
    return `${value.toFixed(decimals)}%`;
  },

  /**
   * Formatea ROAS como ratio
   */
  formatROAS: (roas: number): string => {
    return `${roas.toFixed(2)}x`;
  },

  /**
   * Calcula el color para un valor de ROAS
   */
  getROASColor: (roas: number): string => {
    if (roas >= 3.0) return 'text-green-600';
    if (roas >= 2.0) return 'text-yellow-600'; 
    if (roas >= 1.0) return 'text-orange-600';
    return 'text-red-600';
  },

  /**
   * Calcula el estado de performance basado en ROAS
   */
  getPerformanceStatus: (roas: number): 'excellent' | 'good' | 'warning' | 'poor' => {
    if (roas >= 3.0) return 'excellent';
    if (roas >= 2.0) return 'good';
    if (roas >= 1.0) return 'warning';
    return 'poor';
  },

  /**
   * Calcula tendencia entre dos valores
   */
  calculateTrend: (current: number, previous: number): {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
  } => {
    if (previous === 0) return { direction: 'stable', percentage: 0 };
    
    const change = ((current - previous) / previous) * 100;
    
    if (Math.abs(change) < 1) return { direction: 'stable', percentage: 0 };
    
    return {
      direction: change > 0 ? 'up' : 'down',
      percentage: Math.abs(change)
    };
  },

  /**
   * Agrupa insights por período (día, semana, mes)
   */
  groupInsightsByPeriod: (
    insights: InsightResponse[], 
    period: 'day' | 'week' | 'month'
  ): Record<string, InsightResponse[]> => {
    return insights.reduce((groups, insight) => {
      const date = new Date(insight.date_start);
      let key: string;
      
      switch (period) {
        case 'day':
          key = date.toISOString().split('T')[0];
          break;
        case 'week':
          const startOfWeek = new Date(date);
          startOfWeek.setDate(date.getDate() - date.getDay());
          key = startOfWeek.toISOString().split('T')[0];
          break;
        case 'month':
          key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          break;
        default:
          key = date.toISOString().split('T')[0];
      }
      
      if (!groups[key]) groups[key] = [];
      groups[key].push(insight);
      
      return groups;
    }, {} as Record<string, InsightResponse[]>);
  }
};