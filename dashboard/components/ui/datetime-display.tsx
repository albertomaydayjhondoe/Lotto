import React from "react"
import { format } from "date-fns"

interface DateTimeDisplayProps {
  date: string | Date | null
  formatString?: string
  className?: string
}

export function DateTimeDisplay({ 
  date, 
  formatString = "MMM dd, yyyy HH:mm",
  className 
}: DateTimeDisplayProps) {
  if (!date) {
    return <span className={className}>-</span>
  }

  try {
    const dateObj = typeof date === "string" ? new Date(date) : date
    return (
      <span className={className}>
        {format(dateObj, formatString)}
      </span>
    )
  } catch (error) {
    return <span className={className}>Invalid date</span>
  }
}
