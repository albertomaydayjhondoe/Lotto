/**
 * Recommendation Card Component
 * 
 * Displays an AI recommendation with execute button.
 */

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Recommendation } from "@/lib/ai/api"
import { AlertCircle, Info, XCircle } from "lucide-react"

interface RecommendationCardProps {
  recommendation: Recommendation
  onExecute: (recommendation: Recommendation) => void
  isExecuting?: boolean
}

export function RecommendationCard({ recommendation, onExecute, isExecuting }: RecommendationCardProps) {
  const severityConfig = {
    info: {
      icon: Info,
      variant: "default" as const,
      color: "text-blue-600",
      bgColor: "bg-blue-50"
    },
    warning: {
      icon: AlertCircle,
      variant: "warning" as const,
      color: "text-yellow-600",
      bgColor: "bg-yellow-50"
    },
    critical: {
      icon: XCircle,
      variant: "destructive" as const,
      color: "text-red-600",
      bgColor: "bg-red-50"
    }
  }

  const config = severityConfig[recommendation.severity]
  const Icon = config.icon

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="text-base">{recommendation.title}</CardTitle>
            <CardDescription>{recommendation.description}</CardDescription>
          </div>
          <div className={`${config.bgColor} p-2 rounded-lg ml-4`}>
            <Icon className={`h-5 w-5 ${config.color}`} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          <Badge variant={config.variant}>{recommendation.severity.toUpperCase()}</Badge>
          <Badge variant="outline">{recommendation.action.replace(/_/g, " ")}</Badge>
        </div>
      </CardContent>
      <CardFooter>
        <Button 
          onClick={() => onExecute(recommendation)} 
          disabled={isExecuting}
          className="w-full"
        >
          {isExecuting ? "Executing..." : "Execute"}
        </Button>
      </CardFooter>
    </Card>
  )
}
