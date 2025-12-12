import { useQuery } from "@tanstack/react-query"
import { dashboardApi } from "@/lib/api"

export function useDashboardCampaigns() {
  return useQuery({
    queryKey: ["dashboard", "campaigns"],
    queryFn: dashboardApi.getCampaigns,
  })
}
