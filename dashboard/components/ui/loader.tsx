import React from "react"
import { cn } from "@/lib/utils"

interface LoaderProps {
  className?: string
  size?: "sm" | "md" | "lg"
}

export function Loader({ className, size = "md" }: LoaderProps) {
  const sizeClasses = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-3",
    lg: "h-12 w-12 border-4"
  }

  return (
    <div className={cn("flex items-center justify-center", className)}>
      <div
        className={cn(
          "animate-spin rounded-full border-solid border-primary border-t-transparent",
          sizeClasses[size]
        )}
      />
    </div>
  )
}
