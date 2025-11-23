/**
 * History Status Badge Component
 * 
 * Displays color-coded status badges for AI reasoning runs (PASO 8.2).
 */

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface HistoryStatusBadgeProps {
  status: "ok" | "degraded" | "critical"
  className?: string
}

const statusConfig = {
  ok: {
    label: "OK",
    variant: "success" as const,
    className: "bg-green-500 hover:bg-green-600",
  },
  degraded: {
    label: "Degraded",
    variant: "warning" as const,
    className: "bg-yellow-500 hover:bg-yellow-600",
  },
  critical: {
    label: "Critical",
    variant: "destructive" as const,
    className: "bg-red-500 hover:bg-red-600",
  },
}

export function HistoryStatusBadge({ status, className }: HistoryStatusBadgeProps) {
  const config = statusConfig[status]
  
  return (
    <Badge 
      variant={config.variant}
      className={cn(config.className, className)}
    >
      {config.label}
    </Badge>
  )
}

export default HistoryStatusBadge
