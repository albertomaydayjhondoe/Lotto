/**
 * AlertCard Component
 * 
 * Displays an individual alert with color coding by severity.
 */

'use client';

import { Alert } from '@/lib/alerts/api';
import { useMarkAlertRead } from '@/lib/alerts/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  CheckCircle 
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface AlertCardProps {
  alert: Alert;
}

/**
 * Get color classes based on severity
 */
function getSeverityColor(severity: string): {
  cardBorder: string;
  badgeVariant: 'default' | 'secondary' | 'destructive';
  icon: React.ReactNode;
} {
  switch (severity) {
    case 'CRITICAL':
      return {
        cardBorder: 'border-red-500 border-l-4',
        badgeVariant: 'destructive',
        icon: <AlertCircle className="h-5 w-5 text-red-500" />,
      };
    case 'WARNING':
      return {
        cardBorder: 'border-yellow-500 border-l-4',
        badgeVariant: 'secondary',
        icon: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
      };
    case 'INFO':
    default:
      return {
        cardBorder: 'border-blue-500 border-l-4',
        badgeVariant: 'default',
        icon: <Info className="h-5 w-5 text-blue-500" />,
      };
  }
}

/**
 * Format alert type for display
 */
function formatAlertType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function AlertCard({ alert }: AlertCardProps) {
  const markAsRead = useMarkAlertRead();
  const { cardBorder, badgeVariant, icon } = getSeverityColor(alert.severity);

  const handleMarkAsRead = () => {
    markAsRead.mutate(alert.id);
  };

  return (
    <Card 
      className={`${cardBorder} ${alert.read ? 'opacity-60' : ''} transition-opacity`}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {icon}
            <CardTitle className="text-base">
              {formatAlertType(alert.alert_type)}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={badgeVariant}>
              {alert.severity}
            </Badge>
            {alert.read && (
              <CheckCircle className="h-4 w-4 text-green-500" />
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-sm text-muted-foreground mb-3">
          {alert.message}
        </p>
        
        {alert.metadata && Object.keys(alert.metadata).length > 0 && (
          <div className="bg-muted rounded-md p-2 mb-3">
            <p className="text-xs font-mono text-muted-foreground">
              {JSON.stringify(alert.metadata, null, 2)}
            </p>
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
          </span>
          
          {!alert.read && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleMarkAsRead}
              disabled={markAsRead.isPending}
            >
              Mark as Read
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
