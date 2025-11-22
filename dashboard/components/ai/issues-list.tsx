/**
 * Issues List Component
 * 
 * Displays detected system issues with severity indicators.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Info, XCircle } from "lucide-react"

interface Issue {
  severity: "info" | "warning" | "critical"
  title: string
  description: string
}

interface IssuesListProps {
  issues: Issue[]
}

export function IssuesList({ issues }: IssuesListProps) {
  const severityConfig = {
    info: {
      icon: Info,
      variant: "default" as const,
      color: "text-blue-600"
    },
    warning: {
      icon: AlertCircle,
      variant: "warning" as const,
      color: "text-yellow-600"
    },
    critical: {
      icon: XCircle,
      variant: "destructive" as const,
      color: "text-red-600"
    }
  }

  if (issues.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Issues</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <div className="text-center">
              <Info className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No issues detected</p>
              <p className="text-sm">System running smoothly</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Detected Issues ({issues.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {issues.map((issue, index) => {
            const config = severityConfig[issue.severity]
            const Icon = config.icon

            return (
              <div 
                key={index} 
                className="flex items-start gap-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <Icon className={`h-5 w-5 ${config.color} flex-shrink-0 mt-0.5`} />
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={config.variant} className="text-xs">
                      {issue.severity.toUpperCase()}
                    </Badge>
                    <p className="font-medium text-sm">{issue.title}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">{issue.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
