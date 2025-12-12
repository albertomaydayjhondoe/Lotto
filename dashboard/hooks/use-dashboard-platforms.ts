import { useQuery } from "@tanstack/react-query"
import { dashboardApi } from "@/lib/api"

export function useDashboardPlatforms() {
  return useQuery({
    queryKey: ["dashboard", "platforms"],
    queryFn: dashboardApi.getPlatforms,
  })
}
