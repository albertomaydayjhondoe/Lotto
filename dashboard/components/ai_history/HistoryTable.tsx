/**
 * History Table Component
 * 
 * Displays AI reasoning history in tabular format (PASO 8.2).
 */

"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { HistoryStatusBadge } from "./HistoryStatusBadge"
import type { AIHistoryItem } from "@/lib/ai_history/types"
import { formatDistanceToNow } from "date-fns"

interface HistoryTableProps {
  items: AIHistoryItem[]
  isLoading?: boolean
  className?: string
}

export function HistoryTable({ items, isLoading, className }: HistoryTableProps) {
  if (isLoading) {
    return (
      <div className="text-center py-8 text-gray-500">
        Loading history...
      </div>
    )
  }

  if (!items || items.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No history items found. The AI worker will start generating history automatically.
      </div>
    )
  }

  return (
    <div className={className}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Timestamp</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Recommendations</TableHead>
            <TableHead className="text-right">Critical Issues</TableHead>
            <TableHead>Triggered By</TableHead>
            <TableHead className="text-right">Duration</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="font-medium">
                <div className="flex flex-col">
                  <span className="text-sm">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{item.health_score}</span>
                  <span className="text-gray-500 text-sm">/ 100</span>
                </div>
              </TableCell>
              <TableCell>
                <HistoryStatusBadge status={item.status} />
              </TableCell>
              <TableCell className="text-right">
                {item.recommendations_count}
              </TableCell>
              <TableCell className="text-right">
                {item.critical_issues_count > 0 ? (
                  <span className="text-red-600 font-semibold">
                    {item.critical_issues_count}
                  </span>
                ) : (
                  <span className="text-gray-400">0</span>
                )}
              </TableCell>
              <TableCell>
                <span className="text-xs px-2 py-1 rounded bg-gray-100">
                  {item.triggered_by}
                </span>
              </TableCell>
              <TableCell className="text-right text-sm text-gray-600">
                {item.duration_ms ? `${item.duration_ms}ms` : "N/A"}
              </TableCell>
              <TableCell className="text-right">
                <Link href={`/ai/history/${item.id}`}>
                  <Button variant="outline" size="sm">
                    View
                  </Button>
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export default HistoryTable
