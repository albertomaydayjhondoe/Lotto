import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '@/app/dashboard/page'
import { dashboardApi } from '@/lib/api'

jest.mock('@/lib/api')
jest.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({ isAuthenticated: true, logout: jest.fn() })
}))

const mockOverviewData = {
  total_videos: 150,
  total_clips: 450,
  total_publications: 1200,
  pending_publications: 45,
  active_jobs: 12,
  active_campaigns: 8,
  avg_processing_time_ms: 3500,
  success_rate: 95.5,
  failed_publications: 15,
  avg_visual_score: 8.7,
}

describe('Dashboard Overview Page', () => {
  beforeEach(() => {
    ;(dashboardApi.getOverview as jest.Mock).mockResolvedValue(mockOverviewData)
  })

  it('renders loading state initially', () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <DashboardPage />
      </QueryClientProvider>
    )

    // Check for loader by looking for the spinner div
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders overview stats after loading', async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <DashboardPage />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument() // Total Videos
      expect(screen.getByText('450')).toBeInTheDocument() // Total Clips
      expect(screen.getByText('1200')).toBeInTheDocument() // Total Publications
    })
  })

  it('displays stats cards with correct titles', async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <DashboardPage />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Total Videos')).toBeInTheDocument()
      expect(screen.getByText('Total Clips')).toBeInTheDocument()
      expect(screen.getByText('Total Publications')).toBeInTheDocument()
      expect(screen.getByText('Pending Publications')).toBeInTheDocument()
      expect(screen.getByText('Active Jobs')).toBeInTheDocument()
      expect(screen.getByText('Active Campaigns')).toBeInTheDocument()
    })
  })
})
