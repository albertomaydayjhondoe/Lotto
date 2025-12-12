import { useQuery } from "@tanstack/react-query"
import { dashboardApi } from "@/lib/api"

export function useDashboardOrchestrator() {
  return useQuery({
    queryKey: ["dashboard", "orchestrator"],
    queryFn: dashboardApi.getOrchestrator,
  })
}
