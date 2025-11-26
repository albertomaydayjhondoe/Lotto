// dashboard/lib/meta_insights/hooks.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  getInsightsOverview,
  getCampaignInsights,
  getAdsetInsights,
  getAdInsights,
  getRecentInsights,
  syncInsightsNow,
  type InsightsOverviewResponse,
  type CampaignInsightsOverview,
  type AdsetInsightsOverview,
  type AdInsightsOverview,
  type InsightTimeline,
  type SyncReport,
  type ManualSyncRequest
} from './api';

// Query keys para React Query
export const metaInsightsKeys = {
  all: ['meta-insights'] as const,
  overview: (days: number) => [...metaInsightsKeys.all, 'overview', days] as const,
  campaign: (campaignId: string, days: number) => [...metaInsightsKeys.all, 'campaign', campaignId, days] as const,
  adset: (adsetId: string, days: number) => [...metaInsightsKeys.all, 'adset', adsetId, days] as const,
  ad: (adId: string, days: number) => [...metaInsightsKeys.all, 'ad', adId, days] as const,
  recent: (entityId: string, entityType: string, days: number) => 
    [...metaInsightsKeys.all, 'recent', entityId, entityType, days] as const,
};

/**
 * Hook para obtener vista general de insights
 */
export function useInsightsOverview(days: number = 7) {
  return useQuery({
    queryKey: metaInsightsKeys.overview(days),
    queryFn: () => getInsightsOverview(days),
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 10 * 60 * 1000,   // 10 minutos (antes cacheTime)
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      // No reintentar en errores de autenticación
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        return false;
      }
      return failureCount < 2;
    }
  });
}

/**
 * Hook para obtener insights de una campaña específica
 */
export function useCampaignInsights(campaignId: string, days: number = 30) {
  return useQuery({
    queryKey: metaInsightsKeys.campaign(campaignId, days),
    queryFn: () => getCampaignInsights(campaignId, days),
    enabled: !!campaignId,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 404) return false;
      if (error?.response?.status === 401 || error?.response?.status === 403) return false;
      return failureCount < 2;
    }
  });
}

/**
 * Hook para obtener insights de un adset específico
 */
export function useAdsetInsights(adsetId: string, days: number = 30) {
  return useQuery({
    queryKey: metaInsightsKeys.adset(adsetId, days),
    queryFn: () => getAdsetInsights(adsetId, days),
    enabled: !!adsetId,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 404) return false;
      if (error?.response?.status === 401 || error?.response?.status === 403) return false;
      return failureCount < 2;
    }
  });
}

/**
 * Hook para obtener insights de un ad específico
 */
export function useAdInsights(adId: string, days: number = 30) {
  return useQuery({
    queryKey: metaInsightsKeys.ad(adId, days),
    queryFn: () => getAdInsights(adId, days),
    enabled: !!adId,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 404) return false;
      if (error?.response?.status === 401 || error?.response?.status === 403) return false;
      return failureCount < 2;
    }
  });
}

/**
 * Hook para obtener insights recientes de una entidad
 */
export function useRecentInsights(
  entityId: string,
  entityType: 'campaign' | 'adset' | 'ad',
  days: number = 30
) {
  return useQuery({
    queryKey: metaInsightsKeys.recent(entityId, entityType, days),
    queryFn: () => getRecentInsights(entityId, entityType, days),
    enabled: !!entityId && !!entityType,
    staleTime: 3 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 404) return false;
      if (error?.response?.status === 401 || error?.response?.status === 403) return false;
      return failureCount < 2;
    }
  });
}

/**
 * Hook para ejecutar sincronización manual de insights
 */
export function useSyncInsights() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ManualSyncRequest = {}) => syncInsightsNow(request),
    onSuccess: (data: SyncReport) => {
      // Invalidar todas las queries de insights después de una sincronización exitosa
      queryClient.invalidateQueries({
        queryKey: metaInsightsKeys.all
      });
      
      // Log del resultado de la sincronización
      console.log('Sync completed:', {
        success: data.success,
        duration: data.total_duration_seconds,
        campaigns: data.campaigns.success,
        adsets: data.adsets.success,
        ads: data.ads.success,
        errors: data.errors.length
      });
    },
    onError: (error) => {
      console.error('Sync failed:', error);
    },
    // Configurar retry para mutations
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 401 || error?.response?.status === 403) return false;
      return failureCount < 1; // Solo 1 reintento para sincronización
    }
  });
}

/**
 * Hook personalizado para refrescar datos de insights
 */
export function useRefreshInsights() {
  const queryClient = useQueryClient();

  const refreshOverview = (days?: number) => {
    if (days) {
      queryClient.invalidateQueries({
        queryKey: metaInsightsKeys.overview(days)
      });
    } else {
      queryClient.invalidateQueries({
        queryKey: metaInsightsKeys.all
      });
    }
  };

  const refreshCampaign = (campaignId: string, days?: number) => {
    if (days) {
      queryClient.invalidateQueries({
        queryKey: metaInsightsKeys.campaign(campaignId, days)
      });
    } else {
      queryClient.invalidateQueries({
        predicate: (query) => 
          query.queryKey[0] === 'meta-insights' &&
          query.queryKey[1] === 'campaign' &&
          query.queryKey[2] === campaignId
      });
    }
  };

  const refreshAdset = (adsetId: string, days?: number) => {
    if (days) {
      queryClient.invalidateQueries({
        queryKey: metaInsightsKeys.adset(adsetId, days)
      });
    } else {
      queryClient.invalidateQueries({
        predicate: (query) =>
          query.queryKey[0] === 'meta-insights' &&
          query.queryKey[1] === 'adset' &&
          query.queryKey[2] === adsetId
      });
    }
  };

  const refreshAd = (adId: string, days?: number) => {
    if (days) {
      queryClient.invalidateQueries({
        queryKey: metaInsightsKeys.ad(adId, days)
      });
    } else {
      queryClient.invalidateQueries({
        predicate: (query) =>
          query.queryKey[0] === 'meta-insights' &&
          query.queryKey[1] === 'ad' &&
          query.queryKey[2] === adId
      });
    }
  };

  const refreshAll = () => {
    queryClient.invalidateQueries({
      queryKey: metaInsightsKeys.all
    });
  };

  return {
    refreshOverview,
    refreshCampaign,
    refreshAdset,
    refreshAd,
    refreshAll
  };
}

/**
 * Hook para obtener estado de loading agregado
 */
export function useInsightsLoadingState(
  overviewDays?: number,
  campaignId?: string,
  campaignDays?: number,
  adsetId?: string,
  adsetDays?: number,
  adId?: string,
  adDays?: number
) {
  const overview = useInsightsOverview(overviewDays || 7);
  const campaign = useCampaignInsights(campaignId || '', campaignDays || 30);
  const adset = useAdsetInsights(adsetId || '', adsetDays || 30);
  const ad = useAdInsights(adId || '', adDays || 30);

  const isLoading = overview.isLoading || 
    (campaignId ? campaign.isLoading : false) ||
    (adsetId ? adset.isLoading : false) ||
    (adId ? ad.isLoading : false);

  const isError = overview.isError ||
    (campaignId ? campaign.isError : false) ||
    (adsetId ? adset.isError : false) ||
    (adId ? ad.isError : false);

  const hasData = overview.data ||
    (campaignId ? campaign.data : true) ||
    (adsetId ? adset.data : true) ||
    (adId ? ad.data : true);

  return {
    isLoading,
    isError,
    hasData,
    overview: overview.data,
    campaign: campaign.data,
    adset: adset.data,
    ad: ad.data
  };
}

/**
 * Hook para estadísticas y comparaciones de insights
 */
export function useInsightsStats(timeline?: InsightTimeline) {
  if (!timeline?.insights || timeline.insights.length === 0) {
    return {
      dailyAverage: null,
      weeklyAverage: null,
      bestDay: null,
      worstDay: null,
      trend: null
    };
  }

  const insights = timeline.insights;
  const totalDays = insights.length;

  // Promedios
  const dailyAverage = {
    spend: timeline.total_spend / totalDays,
    impressions: timeline.total_impressions / totalDays,
    clicks: timeline.total_clicks / totalDays,
    conversions: timeline.total_conversions / totalDays,
    revenue: timeline.total_revenue / totalDays
  };

  const weeklyAverage = {
    spend: dailyAverage.spend * 7,
    impressions: dailyAverage.impressions * 7,
    clicks: dailyAverage.clicks * 7,
    conversions: dailyAverage.conversions * 7,
    revenue: dailyAverage.revenue * 7
  };

  // Mejor y peor día por ROAS
  const sortedByROAS = [...insights].sort((a, b) => b.metrics.roas - a.metrics.roas);
  const bestDay = sortedByROAS[0];
  const worstDay = sortedByROAS[sortedByROAS.length - 1];

  // Calcular tendencia (últimos 7 días vs anteriores)
  const trend = insights.length >= 14 ? (() => {
    const recent = insights.slice(0, 7);
    const previous = insights.slice(7, 14);
    
    const recentAvgROAS = recent.reduce((sum, i) => sum + i.metrics.roas, 0) / recent.length;
    const previousAvgROAS = previous.reduce((sum, i) => sum + i.metrics.roas, 0) / previous.length;
    
    const change = ((recentAvgROAS - previousAvgROAS) / previousAvgROAS) * 100;
    
    return {
      direction: change > 0 ? 'up' : 'down',
      percentage: Math.abs(change),
      current: recentAvgROAS,
      previous: previousAvgROAS
    };
  })() : null;

  return {
    dailyAverage,
    weeklyAverage,
    bestDay,
    worstDay,
    trend
  };
}

/**
 * Hook para detectar anomalías en insights
 */
export function useInsightsAnomalies(timeline?: InsightTimeline) {
  if (!timeline?.insights || timeline.insights.length < 7) {
    return { anomalies: [], hasAnomalies: false };
  }

  const insights = timeline.insights;
  const anomalies: Array<{
    date: string;
    metric: string;
    value: number;
    expected: number;
    deviation: number;
    severity: 'low' | 'medium' | 'high';
  }> = [];

  // Calcular medias y desviaciones estándar para métricas clave
  const metrics = ['roas', 'ctr', 'cpc'] as const;
  
  metrics.forEach(metric => {
    const values = insights.map(i => i.metrics[metric]);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    
    // Detectar outliers (> 2 desviaciones estándar)
    insights.forEach(insight => {
      const value = insight.metrics[metric];
      const deviation = Math.abs(value - mean) / stdDev;
      
      if (deviation > 2) {
        anomalies.push({
          date: insight.date_start,
          metric,
          value,
          expected: mean,
          deviation,
          severity: deviation > 3 ? 'high' : deviation > 2.5 ? 'medium' : 'low'
        });
      }
    });
  });

  return {
    anomalies,
    hasAnomalies: anomalies.length > 0
  };
}

/**
 * Hook para obtener resumen de insights (PASO 10.7)
 */
export function useInsightsSummary() {
  return useQuery({
    queryKey: [...metaInsightsKeys.all, "summary"] as const,
    queryFn: async () => {
      const { getInsightsSummary } = await import("./api");
      return getInsightsSummary();
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false
  });
}

/**
 * Hook para obtener info de última sincronización (PASO 10.7)
 */
export function useLastSyncInfo() {
  return useQuery({
    queryKey: [...metaInsightsKeys.all, "last-sync"] as const,
    queryFn: async () => {
      const { getLastSyncInfo } = await import("./api");
      return getLastSyncInfo();
    },
    staleTime: 1 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
    refetchInterval: 60 * 1000
  });
}

/**
 * Hook para ejecutar sincronización completa (PASO 10.7)
 */
export function useRunFullSync() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (daysBack: number = 7) => {
      const { runFullSync } = await import("./api");
      return runFullSync(daysBack);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: metaInsightsKeys.all });
    }
  });
}

/**
 * Hook para sincronizar campaña específica (PASO 10.7)
 */
export function useSyncCampaign() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ campaignId, daysBack = 7 }: { campaignId: string; daysBack?: number }) => {
      const { syncCampaign } = await import("./api");
      return syncCampaign(campaignId, daysBack);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: metaInsightsKeys.campaign(variables.campaignId, variables.daysBack || 7) 
      });
      queryClient.invalidateQueries({ queryKey: [...metaInsightsKeys.all, "summary"] });
    }
  });
}

/**
 * Hook para sincronizar adset específico (PASO 10.7)
 */
export function useSyncAdset() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ adsetId, daysBack = 7 }: { adsetId: string; daysBack?: number }) => {
      const { syncAdset } = await import("./api");
      return syncAdset(adsetId, daysBack);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: metaInsightsKeys.adset(variables.adsetId, variables.daysBack || 7) 
      });
      queryClient.invalidateQueries({ queryKey: [...metaInsightsKeys.all, "summary"] });
    }
  });
}

/**
 * Hook para sincronizar ad específico (PASO 10.7)
 */
export function useSyncAd() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ adId, daysBack = 7 }: { adId: string; daysBack?: number }) => {
      const { syncAd } = await import("./api");
      return syncAd(adId, daysBack);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: metaInsightsKeys.ad(variables.adId, variables.daysBack || 7) 
      });
      queryClient.invalidateQueries({ queryKey: [...metaInsightsKeys.all, "summary"] });
    }
  });
}
