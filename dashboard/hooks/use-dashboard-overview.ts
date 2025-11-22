import { useQuery } from "@tanstack/react-query"
import { dashboardApi } from "@/lib/api"

export function useDashboardOverview() {
  return useQuery({
    queryKey: ["dashboard", "overview"],
    queryFn: dashboardApi.getOverview,
  })
}
