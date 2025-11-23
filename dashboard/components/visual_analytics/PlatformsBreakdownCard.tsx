/**
 * PlatformsBreakdownCard Component (PASO 8.4)
 * 
 * Displays platform performance breakdown
 */

'use client';

import { ChartCard } from './ChartCard';
import { PieChartWidget } from './PieChartWidget';
import type { PlatformStats } from '@/lib/visual_analytics/types';
import { Instagram, Music2, Youtube } from 'lucide-react';

export interface PlatformsBreakdownCardProps {
  data: PlatformStats;
}

const platformIcons: Record<string, any> = {
  instagram: Instagram,
  tiktok: Music2,
  youtube: Youtube,
};

const platformColors: Record<string, string> = {
  instagram: '#E4405F',
  tiktok: '#000000',
  youtube: '#FF0000',
};

export function PlatformsBreakdownCard({ data }: PlatformsBreakdownCardProps) {
  const chartData = data.platforms.map(p => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    value: p.publications_count,
    color: platformColors[p.platform] || '#3b82f6',
  }));

  return (
    <ChartCard
      title="Platform Distribution"
      description="Publications by platform"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <PieChartWidget data={chartData} height={250} />
        </div>
        <div className="space-y-4">
          {data.platforms.map(platform => {
            const Icon = platformIcons[platform.platform];
            return (
              <div
                key={platform.platform}
                className="flex items-center justify-between rounded-lg border p-4"
              >
                <div className="flex items-center gap-3">
                  {Icon && <Icon className="h-5 w-5" style={{ color: platformColors[platform.platform] }} />}
                  <div>
                    <p className="font-medium capitalize">{platform.platform}</p>
                    <p className="text-sm text-muted-foreground">
                      {platform.clips_count} clips · {platform.publications_count} publications
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">{platform.avg_score.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">avg score</p>
                </div>
              </div>
            );
          })}
          {data.best_platform && (
            <div className="mt-4 rounded-md bg-primary/10 p-3 text-sm">
              <p className="font-medium">🏆 Best Platform</p>
              <p className="text-muted-foreground capitalize">{data.best_platform}</p>
            </div>
          )}
        </div>
      </div>
    </ChartCard>
  );
}
