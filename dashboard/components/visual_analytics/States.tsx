/**
 * Loading, Error, and Empty State Components (PASO 8.4)
 */

'use client';

import { motion } from 'framer-motion';
import { Loader2, AlertCircle, FileQuestion } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface LoadingSkeletonProps {
  className?: string;
  count?: number;
}

export function LoadingSkeleton({ className, count = 1 }: LoadingSkeletonProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse rounded-lg bg-muted h-32"
        />
      ))}
    </div>
  );
}

export interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({ message = 'Loading analytics...', className }: LoadingStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn(
        'flex flex-col items-center justify-center py-12 text-center',
        className
      )}
    >
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="mt-4 text-sm text-muted-foreground">{message}</p>
    </motion.div>
  );
}

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Error loading data',
  message = 'There was a problem loading the analytics data. Please try again.',
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-destructive/20 bg-destructive/5 py-12 text-center',
        className
      )}
    >
      <AlertCircle className="h-12 w-12 text-destructive" />
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Try Again
        </button>
      )}
    </motion.div>
  );
}

export interface EmptyStateProps {
  title?: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  title = 'No data available',
  message = 'There is no analytics data to display for the selected time period.',
  action,
  className,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center',
        className
      )}
    >
      <FileQuestion className="h-12 w-12 text-muted-foreground" />
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        {message}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  );
}

export interface NoPermissionStateProps {
  className?: string;
}

export function NoPermissionState({ className }: NoPermissionStateProps) {
  return (
    <ErrorState
      title="Access Denied"
      message="You don't have permission to view analytics. Contact your administrator to request the 'analytics:read' permission."
      className={className}
    />
  );
}
