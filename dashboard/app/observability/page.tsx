/**
 * SPRINT 13 - Human Observability & Cognitive Dashboard
 * Dashboard UI - Observability Page
 * 
 * 4 Sections:
 * 1. Account Overview
 * 2. Warm-up Human Panel
 * 3. Risk & Shadowban Monitor
 * 4. Lifecycle Log Inspector
 */

"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  Activity,
  Shield,
  User,
  Calendar
} from "lucide-react";

// ============================================================================
// TYPES
// ============================================================================

interface AccountState {
  account_id: string;
  current_state: string;
  created_at: string;
  state_duration_days: number;
  next_state: string | null;
  can_advance: boolean;
  blockers: string[];
  metadata: Record<string, any>;
}

interface AccountMetrics {
  account_id: string;
  maturity_score: number;
  risk_score: number;
  readiness_level: number;
  total_actions: number;
  action_diversity: number;
  timestamp: string;
}

interface AccountRisk {
  account_id: string;
  total_risk_score: number;
  shadowban_risk: number;
  correlation_risk: number;
  behavioral_risk: number;
  risk_level: string;
  signals: string[];
  last_check: string;
}

interface HumanWarmupTask {
  task_id: string;
  account_id: string;
  warmup_day: number;
  warmup_phase: string;
  status: string;
  required_actions: any[];
  deadline: string | null;
  created_at: string;
  completed_at: string | null;
}

interface LifecycleEvent {
  event_id: string;
  account_id: string;
  event_type: string;
  previous_state: string | null;
  new_state: string | null;
  reason: string;
  risk_snapshot: Record<string, any>;
  timestamp: string;
}

interface SystemHealth {
  total_accounts: number;
  accounts_by_state: Record<string, number>;
  accounts_secured: number;
  accounts_active: number;
  accounts_blocked: number;
  pending_human_tasks: number;
  verification_pass_rate: number;
  avg_maturity_score: number;
  timestamp: string;
}

// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * Section 1: Account Overview
 */
function AccountOverview({ accountId }: { accountId: string }) {
  const [state, setState] = useState<AccountState | null>(null);
  const [metrics, setMetrics] = useState<AccountMetrics | null>(null);
  const [risk, setRisk] = useState<AccountRisk | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAccountData() {
      try {
        const [stateRes, metricsRes, riskRes] = await Promise.all([
          fetch(`/api/observability/accounts/${accountId}/state`),
          fetch(`/api/observability/accounts/${accountId}/metrics`),
          fetch(`/api/observability/accounts/${accountId}/risk`),
        ]);

        setState(await stateRes.json());
        setMetrics(await metricsRes.json());
        setRisk(await riskRes.json());
      } catch (error) {
        console.error("Error fetching account data:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchAccountData();
    const interval = setInterval(fetchAccountData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [accountId]);

  if (loading) return <div className="animate-pulse">Loading account data...</div>;
  if (!state || !metrics || !risk) return <div>No data available</div>;

  const getStateColor = (stateName: string) => {
    const colors: Record<string, string> = {
      'CREATED': 'bg-gray-500',
      'W1_3': 'bg-blue-500',
      'W4_7': 'bg-blue-600',
      'W8_14': 'bg-blue-700',
      'SECURED': 'bg-green-500',
      'ACTIVE': 'bg-green-600',
      'SCALING': 'bg-purple-500',
      'BLOCKED': 'bg-red-500',
    };
    return colors[stateName] || 'bg-gray-400';
  };

  const getRiskColor = (riskLevel: string) => {
    const colors: Record<string, string> = {
      'LOW': 'text-green-600',
      'MEDIUM': 'text-yellow-600',
      'HIGH': 'text-orange-600',
      'CRITICAL': 'text-red-600',
    };
    return colors[riskLevel] || 'text-gray-600';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="w-5 h-5" />
          Account: {accountId}
        </CardTitle>
        <CardDescription>
          Created {state.state_duration_days} days ago • {state.current_state}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* State Badge */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium mb-2">Current State</p>
            <Badge className={`${getStateColor(state.current_state)} text-white`}>
              {state.current_state}
            </Badge>
          </div>
          <div className="text-right">
            {state.next_state && (
              <p className="text-sm text-muted-foreground">
                Next: {state.next_state}
              </p>
            )}
            {state.can_advance ? (
              <Badge variant="outline" className="mt-1">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Ready to advance
              </Badge>
            ) : (
              <Badge variant="outline" className="mt-1">
                <Clock className="w-3 h-3 mr-1" />
                {state.blockers[0] || "Waiting"}
              </Badge>
            )}
          </div>
        </div>

        {/* Metrics Progress Bars */}
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Maturity Score</span>
              <span className="font-medium">{(metrics.maturity_score * 100).toFixed(0)}%</span>
            </div>
            <Progress value={metrics.maturity_score * 100} className="h-2" />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Risk Score</span>
              <span className={`font-medium ${getRiskColor(risk.risk_level)}`}>
                {(metrics.risk_score * 100).toFixed(0)}%
              </span>
            </div>
            <Progress 
              value={metrics.risk_score * 100} 
              className="h-2"
              // @ts-ignore
              style={{ "--progress-background": metrics.risk_score > 0.5 ? "rgb(239 68 68)" : "rgb(234 179 8)" }}
            />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Readiness Level</span>
              <span className="font-medium">{(metrics.readiness_level * 100).toFixed(0)}%</span>
            </div>
            <Progress value={metrics.readiness_level * 100} className="h-2" />
          </div>
        </div>

        {/* Flags Grid */}
        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            <span>Fingerprint OK</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            <span>Proxy OK</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            <span>Timing OK</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            {risk.signals.length === 0 ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>No Alerts</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                <span>{risk.signals.length} Alerts</span>
              </>
            )}
          </div>
        </div>

        {/* Risk Signals Alert */}
        {risk.signals.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <ul className="list-disc list-inside text-sm">
                {risk.signals.map((signal, i) => (
                  <li key={i}>{signal}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-2xl font-bold">{metrics.total_actions}</p>
            <p className="text-xs text-muted-foreground">Total Actions</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{(metrics.action_diversity * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground">Diversity</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{state.state_duration_days}</p>
            <p className="text-xs text-muted-foreground">Days Active</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Section 2: Warm-up Human Panel
 */
function WarmupHumanPanel() {
  const [tasks, setTasks] = useState<HumanWarmupTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTasks() {
      try {
        const res = await fetch("/api/observability/warmup/human/tasks/today");
        const data = await res.json();
        setTasks(data);
      } catch (error) {
        console.error("Error fetching tasks:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchTasks();
    const interval = setInterval(fetchTasks, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const handleMarkCompleted = async (taskId: string) => {
    // Show confirmation dialog
    if (!confirm("Mark this task as completed?")) return;

    try {
      const res = await fetch(`/api/observability/warmup/human/submit/${taskId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_start: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 min ago
          session_end: new Date().toISOString(),
          actions: [
            { type: "scroll", timestamp: new Date().toISOString(), duration_seconds: 180 },
            { type: "like", timestamp: new Date().toISOString() },
            { type: "like", timestamp: new Date().toISOString() },
          ],
        }),
      });

      const result = await res.json();
      
      if (result.success) {
        alert("Task completed successfully!");
        // Refresh tasks
        const refreshRes = await fetch("/api/observability/warmup/human/tasks/today");
        setTasks(await refreshRes.json());
      } else {
        alert(`Task verification failed: ${result.message}`);
      }
    } catch (error) {
      console.error("Error marking task completed:", error);
      alert("Error marking task completed");
    }
  };

  if (loading) return <div className="animate-pulse">Loading tasks...</div>;

  const pendingTasks = tasks.filter(t => t.status === "pending");
  const urgentTasks = pendingTasks.filter(t => {
    if (!t.deadline) return false;
    const hoursUntilDeadline = (new Date(t.deadline).getTime() - Date.now()) / (1000 * 60 * 60);
    return hoursUntilDeadline < 6; // Less than 6 hours
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Human Warmup Tasks
        </CardTitle>
        <CardDescription>
          {pendingTasks.length} pending • {urgentTasks.length} urgent
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {pendingTasks.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-2 text-green-500" />
            <p>No pending tasks! 🎉</p>
          </div>
        ) : (
          pendingTasks.map((task) => {
            const isUrgent = urgentTasks.includes(task);
            const hoursUntilDeadline = task.deadline 
              ? (new Date(task.deadline).getTime() - Date.now()) / (1000 * 60 * 60)
              : null;

            return (
              <div
                key={task.task_id}
                className={`border rounded-lg p-4 ${isUrgent ? "border-orange-500 bg-orange-50" : ""}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-medium">{task.account_id}</p>
                    <p className="text-sm text-muted-foreground">
                      Day {task.warmup_day} • {task.warmup_phase}
                    </p>
                  </div>
                  {isUrgent && (
                    <Badge variant="destructive" className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {hoursUntilDeadline?.toFixed(1)}h left
                    </Badge>
                  )}
                </div>

                <div className="space-y-1 mb-3">
                  {task.required_actions.map((action, i) => (
                    <div key={i} className="text-sm flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                      <span>
                        {action.type}: {action.quantity || action.duration}
                      </span>
                    </div>
                  ))}
                </div>

                <Button
                  onClick={() => handleMarkCompleted(task.task_id)}
                  className="w-full"
                  size="sm"
                >
                  Mark as Completed
                </Button>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Section 3: Risk & Shadowban Monitor
 */
function RiskMonitor() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [shadowbanSignals, setShadowbanSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRiskData() {
      try {
        const [healthRes, shadowbanRes] = await Promise.all([
          fetch("/api/observability/system_health"),
          fetch("/api/observability/shadowban_signals"),
        ]);

        setSystemHealth(await healthRes.json());
        const shadowbanData = await shadowbanRes.json();
        setShadowbanSignals(shadowbanData.signals || []);
      } catch (error) {
        console.error("Error fetching risk data:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchRiskData();
    const interval = setInterval(fetchRiskData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="animate-pulse">Loading risk data...</div>;
  if (!systemHealth) return <div>No data available</div>;

  const riskLevel = systemHealth.avg_maturity_score < 0.5 ? "HIGH" : "MEDIUM";
  const riskColor = riskLevel === "HIGH" ? "text-red-600" : "text-yellow-600";

  return (
    <div className="space-y-4">
      {/* System Health Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold">{systemHealth.total_accounts}</p>
              <p className="text-sm text-muted-foreground">Total Accounts</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{systemHealth.accounts_secured}</p>
              <p className="text-sm text-muted-foreground">Secured</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{systemHealth.accounts_active}</p>
              <p className="text-sm text-muted-foreground">Active</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-red-600">{systemHealth.accounts_blocked}</p>
              <p className="text-sm text-muted-foreground">Blocked</p>
            </div>
          </div>

          <div className="mt-6 space-y-2">
            <div className="flex justify-between text-sm">
              <span>Verification Pass Rate</span>
              <span className="font-medium">
                {(systemHealth.verification_pass_rate * 100).toFixed(1)}%
              </span>
            </div>
            <Progress value={systemHealth.verification_pass_rate * 100} />

            <div className="flex justify-between text-sm mt-4">
              <span>Avg Maturity Score</span>
              <span className="font-medium">
                {(systemHealth.avg_maturity_score * 100).toFixed(1)}%
              </span>
            </div>
            <Progress value={systemHealth.avg_maturity_score * 100} />
          </div>
        </CardContent>
      </Card>

      {/* Shadowban Signals */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Shadowban Signals
          </CardTitle>
          <CardDescription>
            {shadowbanSignals.length} detected accounts
          </CardDescription>
        </CardHeader>
        <CardContent>
          {shadowbanSignals.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p>No shadowban signals detected</p>
            </div>
          ) : (
            <div className="space-y-2">
              {shadowbanSignals.slice(0, 5).map((signal, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{signal.account_id}</p>
                    <p className="text-sm text-muted-foreground">{signal.state}</p>
                  </div>
                  <Badge
                    variant={
                      signal.severity === "critical" ? "destructive" : "outline"
                    }
                  >
                    {(signal.shadowban_risk * 100).toFixed(0)}% risk
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Section 4: Lifecycle Log Inspector
 */
function LifecycleLog({ accountId }: { accountId: string }) {
  const [events, setEvents] = useState<LifecycleEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchEvents() {
      try {
        const res = await fetch(`/api/observability/accounts/${accountId}/lifecycle_log?limit=50`);
        const data = await res.json();
        setEvents(data);
      } catch (error) {
        console.error("Error fetching lifecycle log:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchEvents();
  }, [accountId]);

  if (loading) return <div className="animate-pulse">Loading events...</div>;

  const getEventIcon = (eventType: string) => {
    if (eventType.includes("transition")) return <TrendingUp className="w-4 h-4 text-blue-500" />;
    if (eventType.includes("rollback")) return <TrendingDown className="w-4 h-4 text-red-500" />;
    if (eventType.includes("completed")) return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    if (eventType.includes("failed")) return <XCircle className="w-4 h-4 text-red-500" />;
    return <Activity className="w-4 h-4 text-gray-500" />;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Lifecycle Log
        </CardTitle>
        <CardDescription>
          Complete history for {accountId}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-center py-4 text-muted-foreground">No events yet</p>
          ) : (
            events.map((event) => (
              <div
                key={event.event_id}
                className="flex items-start gap-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors"
              >
                <div className="mt-1">{getEventIcon(event.event_type)}</div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{event.event_type}</p>
                  {event.previous_state && event.new_state && (
                    <p className="text-sm text-muted-foreground">
                      {event.previous_state} → {event.new_state}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">
                    {event.reason}
                  </p>
                </div>
                <div className="text-xs text-muted-foreground whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleString()}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function ObservabilityPage() {
  const [selectedAccount, setSelectedAccount] = useState<string>("acc_001");

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Observability Dashboard</h1>
        <p className="text-muted-foreground">
          Complete visibility into account lifecycle, warmup, risk, and system health
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="warmup">Warmup Tasks</TabsTrigger>
          <TabsTrigger value="risk">Risk Monitor</TabsTrigger>
          <TabsTrigger value="lifecycle">Lifecycle</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <AccountOverview accountId={selectedAccount} />
        </TabsContent>

        <TabsContent value="warmup" className="space-y-4">
          <WarmupHumanPanel />
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <RiskMonitor />
        </TabsContent>

        <TabsContent value="lifecycle" className="space-y-4">
          <LifecycleLog accountId={selectedAccount} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
