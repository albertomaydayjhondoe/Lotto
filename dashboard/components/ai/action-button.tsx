/**
 * Action Button Component
 * 
 * Button for manual dashboard actions with loading state.
 */

import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"

interface ActionButtonProps {
  label: string
  onClick: () => void
  isLoading?: boolean
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  icon?: React.ReactNode
  disabled?: boolean
}

export function ActionButton({ 
  label, 
  onClick, 
  isLoading, 
  variant = "default", 
  icon, 
  disabled 
}: ActionButtonProps) {
  return (
    <Button
      variant={variant}
      onClick={onClick}
      disabled={isLoading || disabled}
      className="w-full"
    >
      {isLoading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Processing...
        </>
      ) : (
        <>
          {icon && <span className="mr-2">{icon}</span>}
          {label}
        </>
      )}
    </Button>
  )
}
