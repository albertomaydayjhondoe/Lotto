/**
 * History Filters Component
 * 
 * Filter controls for AI reasoning history (PASO 8.2).
 */

"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import type { AIHistoryFilters } from "@/lib/ai_history/types"

interface HistoryFiltersProps {
  filters: AIHistoryFilters
  onFiltersChange: (filters: AIHistoryFilters) => void
  className?: string
}

export function HistoryFilters({ filters, onFiltersChange, className }: HistoryFiltersProps) {
  const [localFilters, setLocalFilters] = useState<AIHistoryFilters>(filters)

  const handleApply = () => {
    onFiltersChange(localFilters)
  }

  const handleReset = () => {
    const resetFilters: AIHistoryFilters = {}
    setLocalFilters(resetFilters)
    onFiltersChange(resetFilters)
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Score Range */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="min_score">Min Score</Label>
            <Input
              id="min_score"
              type="number"
              min="0"
              max="100"
              placeholder="0"
              value={localFilters.min_score ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setLocalFilters({
                  ...localFilters,
                  min_score: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="max_score">Max Score</Label>
            <Input
              id="max_score"
              type="number"
              min="0"
              max="100"
              placeholder="100"
              value={localFilters.max_score ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setLocalFilters({
                  ...localFilters,
                  max_score: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
          </div>
        </div>

        {/* Status Filter */}
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <Select
            value={localFilters.status ?? "all"}
            onValueChange={(value: string) =>
              setLocalFilters({
                ...localFilters,
                status: value === "all" ? undefined : (value as "ok" | "degraded" | "critical"),
              })
            }
          >
            <SelectTrigger id="status">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="ok">OK</SelectItem>
              <SelectItem value="degraded">Degraded</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="from_date">From Date</Label>
            <Input
              id="from_date"
              type="datetime-local"
              value={localFilters.from_date ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setLocalFilters({
                  ...localFilters,
                  from_date: e.target.value || undefined,
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="to_date">To Date</Label>
            <Input
              id="to_date"
              type="datetime-local"
              value={localFilters.to_date ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setLocalFilters({
                  ...localFilters,
                  to_date: e.target.value || undefined,
                })
              }
            />
          </div>
        </div>

        {/* Critical Only Checkbox */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="only_critical"
            checked={localFilters.only_critical ?? false}
            onCheckedChange={(checked: boolean | 'indeterminate') =>
              setLocalFilters({
                ...localFilters,
                only_critical: checked === true,
              })
            }
          />
          <Label htmlFor="only_critical" className="cursor-pointer">
            Show only critical issues
          </Label>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          <Button onClick={handleApply} className="flex-1">
            Apply Filters
          </Button>
          <Button onClick={handleReset} variant="outline">
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default HistoryFilters
