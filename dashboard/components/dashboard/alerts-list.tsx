/**
 * AlertsList Component
 * 
 * Displays a list of alerts grouped by severity with filtering.
 */

'use client';

import { Alert } from '@/lib/alerts/api';
import { AlertCard } from './alert-card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle } from 'lucide-react';

interface AlertsListProps {
  alerts: Alert[];
  showTabs?: boolean;
}

/**
 * Group alerts by severity
 */
function groupBySeverity(alerts: Alert[]): {
  critical: Alert[];
  warning: Alert[];
  info: Alert[];
} {
  return {
    critical: alerts.filter(a => a.severity === 'CRITICAL'),
    warning: alerts.filter(a => a.severity === 'WARNING'),
    info: alerts.filter(a => a.severity === 'INFO'),
  };
}

/**
 * Empty state component
 */
function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
      <p className="text-muted-foreground">{message}</p>
    </div>
  );
}

export function AlertsList({ alerts, showTabs = false }: AlertsListProps) {
  if (alerts.length === 0) {
    return <EmptyState message="No alerts to display" />;
  }

  if (showTabs) {
    const grouped = groupBySeverity(alerts);

    return (
      <Tabs defaultValue="all" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">
            All ({alerts.length})
          </TabsTrigger>
          <TabsTrigger value="critical">
            Critical ({grouped.critical.length})
          </TabsTrigger>
          <TabsTrigger value="warning">
            Warning ({grouped.warning.length})
          </TabsTrigger>
          <TabsTrigger value="info">
            Info ({grouped.info.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-4">
          {alerts.map(alert => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </TabsContent>

        <TabsContent value="critical" className="space-y-4 mt-4">
          {grouped.critical.length > 0 ? (
            grouped.critical.map(alert => (
              <AlertCard key={alert.id} alert={alert} />
            ))
          ) : (
            <EmptyState message="No critical alerts" />
          )}
        </TabsContent>

        <TabsContent value="warning" className="space-y-4 mt-4">
          {grouped.warning.length > 0 ? (
            grouped.warning.map(alert => (
              <AlertCard key={alert.id} alert={alert} />
            ))
          ) : (
            <EmptyState message="No warning alerts" />
          )}
        </TabsContent>

        <TabsContent value="info" className="space-y-4 mt-4">
          {grouped.info.length > 0 ? (
            grouped.info.map(alert => (
              <AlertCard key={alert.id} alert={alert} />
            ))
          ) : (
            <EmptyState message="No info alerts" />
          )}
        </TabsContent>
      </Tabs>
    );
  }

  // Simple list without tabs
  return (
    <div className="space-y-4">
      {alerts.map(alert => (
        <AlertCard key={alert.id} alert={alert} />
      ))}
    </div>
  );
}
