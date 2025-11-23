/**
 * History Score Card Component
 * 
 * Displays health score with visual indicator (PASO 8.2).
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface HistoryScoreCardProps {
  score: number
  status: "ok" | "degraded" | "critical"
  className?: string
}

function getScoreColor(status: "ok" | "degraded" | "critical"): string {
  switch (status) {
    case "ok":
      return "text-green-600"
    case "degraded":
      return "text-yellow-600"
    case "critical":
      return "text-red-600"
    default:
      return "text-gray-600"
  }
}

function getScoreBgColor(status: "ok" | "degraded" | "critical"): string {
  switch (status) {
    case "ok":
      return "bg-green-100"
    case "degraded":
      return "bg-yellow-100"
    case "critical":
      return "bg-red-100"
    default:
      return "bg-gray-100"
  }
}

export function HistoryScoreCard({ score, status, className }: HistoryScoreCardProps) {
  const colorClass = getScoreColor(status)
  const bgClass = getScoreBgColor(status)
  
  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Health Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={cn("rounded-lg p-6 text-center", bgClass)}>
          <div className={cn("text-5xl font-bold", colorClass)}>
            {score}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            / 100
          </div>
        </div>
        
        {/* Score bar */}
        <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={cn(
              "h-full transition-all duration-300",
              status === "ok" && "bg-green-500",
              status === "degraded" && "bg-yellow-500",
              status === "critical" && "bg-red-500"
            )}
            style={{ width: `${score}%` }}
          />
        </div>
        
        <div className="mt-4 text-center text-xs text-gray-500">
          {status === "ok" && "System performing well"}
          {status === "degraded" && "System needs attention"}
          {status === "critical" && "Immediate action required"}
        </div>
      </CardContent>
    </Card>
  )
}

export default HistoryScoreCard
