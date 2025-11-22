import React from "react"
import { cn } from "@/lib/utils"

interface ChartContainerProps {
  children: React.ReactNode
  className?: string
  title?: string
}

export function ChartContainer({ children, className, title }: ChartContainerProps) {
  return (
    <div className={cn("w-full", className)}>
      {title && (
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
      )}
      <div className="w-full h-full">
        {children}
      </div>
    </div>
  )
}
