/**
 * Alert Center Page
 * 
 * Main page for viewing and managing system alerts.
 */

'use client';

import { useAlerts, useRunAnalysis, useAlertsWebSocket } from '@/lib/alerts/hooks';
import { AlertsList } from '@/components/dashboard/alerts-list';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, AlertCircle, Bell, BellOff } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

export default function AlertsPage() {
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const allAlertsQuery = useAlerts(false);
  const unreadAlertsQuery = useAlerts(true);
  const runAnalysis = useRunAnalysis();

  // WebSocket connection with toast notifications
  const { isConnected, lastAlert } = useAlertsWebSocket((alert) => {
    // Show toast for new alerts
    const severity = alert.severity.toLowerCase();
    const message = alert.message;
    
    if (alert.severity === 'CRITICAL') {
      toast.error(message, {
        description: `Alert type: ${alert.alert_type}`,
        duration: 8000,
      });
    } else if (alert.severity === 'WARNING') {
      toast.warning(message, {
        description: `Alert type: ${alert.alert_type}`,
        duration: 8000,
      });
    } else {
      toast.info(message, {
        description: `Alert type: ${alert.alert_type}`,
        duration: 8000,
      });
    }
  });

  const handleRunAnalysis = () => {
    runAnalysis.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(`Analysis complete: ${data.alerts_generated} alert(s) generated`);
      },
      onError: () => {
        toast.error('Failed to run analysis');
      },
    });
  };

  const currentQuery = filter === 'all' ? allAlertsQuery : unreadAlertsQuery;
  const alerts = currentQuery.data?.alerts || [];
  const unreadCount = unreadAlertsQuery.data?.unread_count || 0;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Alert Center</h1>
          <p className="text-muted-foreground">
            Monitor and manage system alerts in real-time
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* WebSocket Status */}
          <Badge variant={isConnected ? 'default' : 'secondary'}>
            {isConnected ? (
              <>
                <Bell className="h-3 w-3 mr-1" />
                Live
              </>
            ) : (
              <>
                <BellOff className="h-3 w-3 mr-1" />
                Disconnected
              </>
            )}
          </Badge>

          {/* Run Analysis Button */}
          <Button 
            onClick={handleRunAnalysis} 
            disabled={runAnalysis.isPending}
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${runAnalysis.isPending ? 'animate-spin' : ''}`} />
            Run Analysis
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allAlertsQuery.data?.total || 0}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unread</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{unreadCount}</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Connection</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isConnected ? 'Active' : 'Inactive'}</div>
            <p className="text-xs text-muted-foreground">WebSocket status</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts List with Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Alerts</CardTitle>
          <CardDescription>
            View and manage system alerts. Critical alerts require immediate attention.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={filter} onValueChange={(v) => setFilter(v as 'all' | 'unread')}>
            <TabsList>
              <TabsTrigger value="all">
                All ({allAlertsQuery.data?.total || 0})
              </TabsTrigger>
              <TabsTrigger value="unread">
                Unread ({unreadCount})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-4">
              {allAlertsQuery.isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <AlertsList alerts={alerts} showTabs />
              )}
            </TabsContent>

            <TabsContent value="unread" className="mt-4">
              {unreadAlertsQuery.isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <AlertsList alerts={alerts} showTabs />
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
