/**
 * Live Metrics Cards
 * 
 * Displays real-time metrics from telemetry data.
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTelemetry } from "@/lib/live/useTelemetry";
import { 
  Activity, 
  Clock, 
  Zap,
  TrendingUp,
  Users,
  Radio
} from "lucide-react";

export function LiveQueueCard() {
  const { data, isConnected } = useTelemetry();
  
  if (!data) return null;

  const total = data.queue.total;
  const saturation = total > 0 ? (data.queue.pending + data.queue.processing) / total : 0;
  const saturationColor = saturation > 0.7 ? "text-red-600" : saturation > 0.4 ? "text-yellow-600" : "text-green-600";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Queue Status
          {isConnected && <Radio className="h-3 w-3 text-green-500 animate-pulse" />}
        </CardTitle>
        <Activity className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold">{data.queue.pending}</span>
            <span className="text-sm text-muted-foreground">pending</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-muted-foreground">Processing</div>
              <div className="font-semibold text-blue-600">{data.queue.processing}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Success</div>
              <div className="font-semibold text-green-600">{data.queue.success}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Failed</div>
              <div className="font-semibold text-red-600">{data.queue.failed}</div>
            </div>
          </div>
          <div className="pt-1 border-t">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Saturation</span>
              <span className={`font-semibold ${saturationColor}`}>
                {(saturation * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function LiveSchedulerCard() {
  const { data, isConnected } = useTelemetry();
  
  if (!data) return null;

  const avgDelayMins = data.scheduler.avg_delay_seconds 
    ? (data.scheduler.avg_delay_seconds / 60).toFixed(1) 
    : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Scheduler
          {isConnected && <Radio className="h-3 w-3 text-green-500 animate-pulse" />}
        </CardTitle>
        <Clock className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold">{data.scheduler.scheduled_today}</span>
            <span className="text-sm text-muted-foreground">today</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <div className="text-muted-foreground">Next Hour</div>
              <div className="font-semibold text-blue-600">{data.scheduler.scheduled_next_hour}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Overdue</div>
              <div className="font-semibold text-red-600">{data.scheduler.overdue}</div>
            </div>
          </div>
          {avgDelayMins && (
            <div className="pt-1 border-t">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Avg Delay</span>
                <span className="font-semibold text-yellow-600">
                  {avgDelayMins}m
                </span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function LiveOrchestratorCard() {
  const { data, isConnected } = useTelemetry();
  
  if (!data) return null;

  const lastRunMins = data.orchestrator.last_run_seconds_ago 
    ? (data.orchestrator.last_run_seconds_ago / 60).toFixed(1) 
    : null;
  
  const saturation = data.orchestrator.saturation_rate ?? 0;
  const saturationColor = saturation > 0.7 ? "text-red-600" : saturation > 0.4 ? "text-yellow-600" : "text-green-600";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Orchestrator
          {isConnected && <Radio className="h-3 w-3 text-green-500 animate-pulse" />}
        </CardTitle>
        <Zap className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold">{data.orchestrator.actions_last_minute}</span>
            <span className="text-sm text-muted-foreground">actions/min</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <div className="text-muted-foreground">Pending</div>
              <div className="font-semibold text-blue-600">{data.orchestrator.decisions_pending}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Saturation</div>
              <div className={`font-semibold ${saturationColor}`}>
                {(saturation * 100).toFixed(0)}%
              </div>
            </div>
          </div>
          {lastRunMins && (
            <div className="pt-1 border-t">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Last Run</span>
                <span className="font-semibold text-gray-600">
                  {lastRunMins}m ago
                </span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function LivePlatformCard() {
  const { data, isConnected } = useTelemetry();
  
  if (!data) return null;

  const total = data.platforms.instagram + data.platforms.tiktok + 
                data.platforms.youtube + data.platforms.facebook;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Platforms
          {isConnected && <Radio className="h-3 w-3 text-green-500 animate-pulse" />}
        </CardTitle>
        <TrendingUp className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold">{total}</span>
            <span className="text-sm text-muted-foreground">ready</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <div className="text-muted-foreground">Instagram</div>
              <div className="font-semibold text-pink-600">{data.platforms.instagram}</div>
            </div>
            <div>
              <div className="text-muted-foreground">TikTok</div>
              <div className="font-semibold text-black">{data.platforms.tiktok}</div>
            </div>
            <div>
              <div className="text-muted-foreground">YouTube</div>
              <div className="font-semibold text-red-600">{data.platforms.youtube}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Facebook</div>
              <div className="font-semibold text-blue-600">{data.platforms.facebook}</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function LiveWorkerCard() {
  const { data, isConnected } = useTelemetry();
  
  if (!data) return null;

  const avgTimeSec = data.workers.avg_processing_time_ms 
    ? (data.workers.avg_processing_time_ms / 1000).toFixed(1) 
    : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Workers
          {isConnected && <Radio className="h-3 w-3 text-green-500 animate-pulse" />}
        </CardTitle>
        <Users className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold">{data.workers.active_workers}</span>
            <span className="text-sm text-muted-foreground">active</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <div className="text-muted-foreground">Processing</div>
              <div className="font-semibold text-blue-600">{data.workers.tasks_processing}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Avg Time</div>
              <div className="font-semibold text-green-600">
                {avgTimeSec ? `${avgTimeSec}s` : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
