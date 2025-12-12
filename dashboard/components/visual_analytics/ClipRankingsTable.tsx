/**
 * ClipRankingsTable Component (PASO 8.4)
 * 
 * Displays top-performing clips in a table
 */

'use client';

import { ChartCard } from './ChartCard';
import type { ClipRanking } from '@/lib/visual_analytics/types';
import { Trophy, Clock } from 'lucide-react';

export interface ClipRankingsTableProps {
  clips: ClipRanking[];
  title?: string;
  description?: string;
}

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

export function ClipRankingsTable({
  clips,
  title = 'Top Performing Clips',
  description = 'Highest scoring clips',
}: ClipRankingsTableProps) {
  if (!clips || clips.length === 0) {
    return (
      <ChartCard title={title} description={description}>
        <p className="text-center text-muted-foreground py-8">
          No clips data available
        </p>
      </ChartCard>
    );
  }

  return (
    <ChartCard title={title} description={description}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b text-left text-sm text-muted-foreground">
              <th className="pb-3 pr-4 font-medium">Rank</th>
              <th className="pb-3 pr-4 font-medium">Clip ID</th>
              <th className="pb-3 pr-4 font-medium">Score</th>
              <th className="pb-3 font-medium">Duration</th>
            </tr>
          </thead>
          <tbody>
            {clips.map((clip, index) => (
              <tr key={clip.clip_id} className="border-b last:border-0">
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    {index === 0 && <Trophy className="h-4 w-4 text-yellow-500" />}
                    <span className="font-medium">{index + 1}</span>
                  </div>
                </td>
                <td className="py-3 pr-4">
                  <div>
                    <p className="font-mono text-sm">{clip.clip_id.slice(0, 8)}...</p>
                    {clip.title && (
                      <p className="text-xs text-muted-foreground">{clip.title}</p>
                    )}
                  </div>
                </td>
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-20 rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${clip.score * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">{clip.score.toFixed(2)}</span>
                  </div>
                </td>
                <td className="py-3">
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {formatDuration(clip.duration_ms)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ChartCard>
  );
}
