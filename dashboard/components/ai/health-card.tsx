/**
 * Health Card Component
 * 
 * Displays system health status with color coding.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle, XCircle } from "lucide-react"

interface HealthCardProps {
  title: string
  status: "good" | "warning" | "critical"
  description?: string
  metric?: string | number
}

export function HealthCard({ title, status, description, metric }: HealthCardProps) {
  const statusConfig = {
    good: {
      icon: CheckCircle,
      color: "text-green-600",
      bgColor: "bg-green-50",
      badgeVariant: "success" as const,
      label: "Healthy"
    },
    warning: {
      icon: AlertCircle,
      color: "text-yellow-600",
      bgColor: "bg-yellow-50",
      badgeVariant: "warning" as const,
      label: "Warning"
    },
    critical: {
      icon: XCircle,
      color: "text-red-600",
      bgColor: "bg-red-50",
      badgeVariant: "destructive" as const,
      label: "Critical"
    }
  }

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className={`${config.bgColor} p-2 rounded-lg`}>
          <Icon className={`h-4 w-4 ${config.color}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Badge variant={config.badgeVariant}>{config.label}</Badge>
          {metric && (
            <div className="text-2xl font-bold">{metric}</div>
          )}
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
