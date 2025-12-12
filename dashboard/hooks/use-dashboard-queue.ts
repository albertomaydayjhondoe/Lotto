import { useQuery } from "@tanstack/react-query"
import { dashboardApi } from "@/lib/api"

export function useDashboardQueue() {
  return useQuery({
    queryKey: ["dashboard", "queue"],
    queryFn: dashboardApi.getQueue,
  })
}
