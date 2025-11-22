import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import QueuePage from '@/app/dashboard/queue/page'
import { dashboardApi } from '@/lib/api'

jest.mock('@/lib/api')
jest.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({ isAuthenticated: true, logout: jest.fn() })
}))

const mockQueueData = {
  total_in_queue: 48,
  pending: 25,
  scheduled: 15,
  processing: 8,
  avg_wait_time_ms: 4500,
  estimated_completion_time: '2025-11-23T10:30:00Z',
}

describe('Queue Page', () => {
  beforeEach(() => {
    ;(dashboardApi.getQueue as jest.Mock).mockResolvedValue(mockQueueData)
  })

  it('renders queue stats', async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <QueuePage />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('48')).toBeInTheDocument() // Total in queue
      expect(screen.getByText('25')).toBeInTheDocument() // Pending
      expect(screen.getByText('15')).toBeInTheDocument() // Scheduled
    })
  })

  it('renders queue table with items', async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <QueuePage />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Queue Items')).toBeInTheDocument()
      expect(screen.getAllByRole('row').length).toBeGreaterThan(1) // Header + data rows
    })
  })

  it('displays action buttons for queue items', async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <QueuePage />
      </QueryClientProvider>
    )

    await waitFor(() => {
      const forceButtons = screen.getAllByText(/Force/i)
      const retryButtons = screen.getAllByText(/Retry/i)
      expect(forceButtons.length).toBeGreaterThan(0)
      expect(retryButtons.length).toBeGreaterThan(0)
    })
  })
})
