import React from "react"
import { cn } from "@/lib/utils"

interface StatusDotProps {
  status: "pending" | "success" | "failed" | "processing" | "scheduled" | "draft" | "published"
  className?: string
}

export function StatusDot({ status, className }: StatusDotProps) {
  const colors = {
    pending: "bg-blue-500",
    success: "bg-green-500",
    failed: "bg-red-500",
    processing: "bg-yellow-500",
    scheduled: "bg-purple-500",
    draft: "bg-gray-500",
    published: "bg-green-600",
  }

  return (
    <span
      className={cn(
        "inline-block h-2 w-2 rounded-full",
        colors[status],
        className
      )}
    />
  )
}
