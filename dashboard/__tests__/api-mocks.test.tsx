import axios from 'axios'

jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

// Mock API client
const mockGet = jest.fn()
const mockApiClient = {
  get: mockGet,
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  defaults: {},
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn(), clear: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn(), clear: jest.fn() },
  },
}

// Mock axios.create before importing dashboardApi
mockedAxios.create = jest.fn(() => mockApiClient as any)

// Now import dashboardApi
import { dashboardApi } from '@/lib/api'

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('fetches overview stats successfully', async () => {
    const mockData = {
      total_videos: 100,
      total_clips: 300,
      total_publications: 500,
      pending_publications: 20,
      active_jobs: 5,
      active_campaigns: 3,
      avg_processing_time_ms: 2500,
      success_rate: 98.5,
      failed_publications: 5,
      avg_visual_score: 9.2,
    }

    mockGet.mockResolvedValue({ data: mockData })

    const result = await dashboardApi.getOverview()
    expect(result).toEqual(mockData)
    expect(mockGet).toHaveBeenCalledWith('/dashboard/stats/overview')
  })

  it('fetches queue stats successfully', async () => {
    const mockData = {
      total_in_queue: 30,
      pending: 15,
      scheduled: 10,
      processing: 5,
      avg_wait_time_ms: 3000,
      estimated_completion_time: null,
    }

    mockGet.mockResolvedValue({ data: mockData })

    const result = await dashboardApi.getQueue()
    expect(result).toEqual(mockData)
    expect(mockGet).toHaveBeenCalledWith('/dashboard/stats/queue')
  })

  it('handles API errors gracefully', async () => {
    mockGet.mockRejectedValue(new Error('Network error'))

    await expect(dashboardApi.getOverview()).rejects.toThrow('Network error')
  })
})
