# Visual Analytics Dashboard - Frontend Documentation

## 📊 Overview

The Visual Analytics Dashboard is a comprehensive React/Next.js frontend built to consume the analytics endpoints created in PASO 8.3. It provides real-time visualization of system metrics across clips, jobs, publications, campaigns, platforms, and orchestrator activities.

**Status:** ✅ Production Ready  
**Lines of Code:** ~2,100+ TypeScript/React  
**Components:** 13 reusable components  
**Pages:** 7 analytics pages  
**Tests:** 20+ comprehensive tests  

---

## 🏗️ Architecture

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | Next.js 14 (App Router) | SSR, routing, React framework |
| **Language** | TypeScript (strict mode) | Type safety, better DX |
| **Data Fetching** | React Query v5 | Cache, refetch, optimistic updates |
| **Charts** | Recharts 2.x | Line, bar, pie charts |
| **Animations** | Framer Motion | Smooth transitions |
| **UI Components** | Shadcn/ui | Base components (Select, Input, etc.) |
| **Styling** | Tailwind CSS | Utility-first, dark mode |
| **Date Handling** | date-fns | Date formatting, manipulation |

### Architecture Layers

```
┌──────────────────────────────────────────────────────────┐
│                   Presentation Layer                      │
│  app/dashboard/visual/*.tsx (Pages with UI logic)        │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────┐
│                 Data Management Layer                     │
│  lib/visual_analytics/hooks.ts (React Query hooks)       │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────┐
│                      API Layer                            │
│  lib/visual_analytics/api.ts (HTTP client)               │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────┐
│                   Backend API (PASO 8.3)                  │
│  /api/v1/visual_analytics/* (6 endpoints)                │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. User interacts with Page Component (e.g., Overview)
2. Page uses React Query Hook (e.g., useOverviewAnalytics)
3. Hook calls API Client function (e.g., getOverview)
4. API Client makes HTTP request with auth token
5. Backend returns JSON data
6. React Query caches data and returns to hook
7. Page component renders with data
8. Chart components visualize data (Recharts)
```

---

## 📁 Project Structure

```
dashboard/
├── lib/visual_analytics/
│   ├── types.ts                  # TypeScript type definitions (190 lines)
│   ├── api.ts                    # API client functions (189 lines)
│   └── hooks.ts                  # React Query hooks (179 lines)
│
├── components/visual_analytics/
│   ├── index.ts                  # Barrel export
│   ├── StatCard.tsx              # Metric display card (88 lines)
│   ├── ChartCard.tsx             # Chart wrapper (52 lines)
│   ├── States.tsx                # Loading/Error/Empty states (144 lines)
│   ├── LineChartWidget.tsx       # Line chart component (104 lines)
│   ├── BarChartWidget.tsx        # Bar chart component (70 lines)
│   ├── PieChartWidget.tsx        # Pie chart component (69 lines)
│   ├── PlatformsBreakdownCard.tsx # Platform metrics (83 lines)
│   ├── ClipRankingsTable.tsx     # Top clips table (95 lines)
│   ├── OverviewGrid.tsx          # Stats grid layout (85 lines)
│   └── DateRangeFilter.tsx       # Time range selector (55 lines)
│
└── app/dashboard/visual/
    ├── page.tsx                  # Main redirect page (23 lines)
    ├── overview/page.tsx         # Complete overview (138 lines)
    ├── platforms/page.tsx        # Platform performance (114 lines)
    ├── clips/page.tsx            # Clips distribution (122 lines)
    ├── timeline/page.tsx         # Activity timeline (116 lines)
    ├── campaigns/page.tsx        # Campaign metrics (183 lines)
    └── heatmap/page.tsx          # Activity heatmap (120 lines)
```

---

## 🔧 Core Components

### Library Layer

#### **types.ts** - TypeScript Definitions

All TypeScript interfaces that mirror backend Pydantic schemas:

```typescript
// Main response type for overview endpoint
export interface AnalyticsOverview {
  total_clips: number;
  total_jobs: number;
  total_publications: number;
  total_campaigns: number;
  clips_per_week: number;
  clips_per_month: number;
  average_clip_score: number;
  top_clips: ClipRanking[];
  correlations: Record<string, number>;
  rule_engine_metrics: Record<string, number>;
  generated_at: string;
}

// Timeline data with multiple series
export interface TimelineData {
  jobs_timeline: Timeseries[];
  publications_timeline: Timeseries[];
  clips_timeline: Timeseries[];
  orchestrator_timeline: Timeseries[];
}

// Query parameters for all endpoints
export interface AnalyticsQueryParams {
  days?: number;
  start_date?: string;
  end_date?: string;
  platform?: string;
}
```

**Key Types:**
- `AnalyticsOverview` - Main overview response
- `TimelineData` - Timeline series data
- `HeatmapData` - Hour x Day heatmap
- `PlatformStats` - Platform metrics
- `ClipsDistribution` - Clips analytics
- `CampaignBreakdown` - Campaign metrics
- `Timeseries` - Time series point `{timestamp, value}`
- `Distribution` - Distribution bucket `{bucket, count}`
- `ClipRanking` - Top clip `{rank, clip_id, score, duration_seconds}`

#### **api.ts** - API Client

HTTP client with 6 functions for all analytics endpoints:

```typescript
import { AnalyticsQueryParams, AnalyticsOverview } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Build query string from params
function buildQueryString(params: AnalyticsQueryParams): string {
  const searchParams = new URLSearchParams();
  if (params.days) searchParams.append('days', params.days.toString());
  if (params.start_date) searchParams.append('start_date', params.start_date);
  if (params.end_date) searchParams.append('end_date', params.end_date);
  if (params.platform) searchParams.append('platform', params.platform);
  return searchParams.toString();
}

// Fetch with auth token from localStorage
async function fetchWithAuth(url: string): Promise<any> {
  const token = localStorage.getItem('auth_token');
  const response = await fetch(url, {
    headers: {
      Authorization: token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// API functions
export const visualAnalyticsApi = {
  getOverview: (params: AnalyticsQueryParams = {}): Promise<AnalyticsOverview> => {
    const qs = buildQueryString(params);
    return fetchWithAuth(`${BASE_URL}/api/v1/visual_analytics/overview?${qs}`);
  },
  // ... 5 more functions
};
```

**Available Functions:**
- `getOverview(params)` - Complete analytics overview
- `getTimeline(params)` - Timeline data (4 series)
- `getHeatmap(params)` - Heatmap matrix (24h x 7d)
- `getPlatformStats(params)` - Platform metrics
- `getClipsDistribution(params)` - Clips analytics
- `getCampaignBreakdown(params)` - Campaign metrics

**Features:**
- Bearer token authentication from localStorage
- Query string building helper
- Error handling (throws on non-2xx)
- TypeScript return types

#### **hooks.ts** - React Query Hooks

React Query hooks for data fetching and caching:

```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { visualAnalyticsApi } from './api';
import { AnalyticsQueryParams, AnalyticsOverview } from './types';

// Cache key factory
export const analyticsKeys = {
  all: ['analytics'] as const,
  overview: (params: AnalyticsQueryParams) => ['analytics', 'overview', params] as const,
  timeline: (params: AnalyticsQueryParams) => ['analytics', 'timeline', params] as const,
  // ... more keys
};

// Hook for overview analytics
export function useOverviewAnalytics(params: AnalyticsQueryParams = {}) {
  return useQuery({
    queryKey: analyticsKeys.overview(params),
    queryFn: () => visualAnalyticsApi.getOverview(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,   // 10 minutes
  });
}

// ... 5 more hooks

// Prefetch hook for performance
export function usePrefetchAnalytics() {
  const queryClient = useQueryClient();
  
  return (params: AnalyticsQueryParams = {}) => {
    queryClient.prefetchQuery({
      queryKey: analyticsKeys.overview(params),
      queryFn: () => visualAnalyticsApi.getOverview(params),
    });
  };
}
```

**Available Hooks:**
- `useOverviewAnalytics(params)` - staleTime: 5min
- `useTimelineAnalytics(params)` - staleTime: 2min
- `useHeatmapAnalytics(params)` - staleTime: 5min
- `usePlatformAnalytics(params)` - staleTime: 5min
- `useClipsAnalytics(params)` - staleTime: 5min
- `useCampaignAnalytics(params)` - staleTime: 5min
- `usePrefetchAnalytics()` - Prefetch helper

**Features:**
- Cache key management with `analyticsKeys`
- Proper stale time (2-5 minutes)
- Garbage collection time (5-10 minutes)
- `enabled` option for conditional fetching
- Prefetch support for performance

---

### Component Layer

#### **StatCard** - Metric Display Card

Display a single metric with optional trend indicator:

```tsx
import { StatCard } from '@/components/visual_analytics';
import { TrendingUp, Video } from 'lucide-react';

<StatCard
  title="Total Clips"
  value={1234}
  subtitle="Last 30 days"
  icon={Video}
  trend={{ value: 12.5, direction: 'up' }}
  color="blue"
/>
```

**Props:**
- `title: string` - Card title
- `value: number | string` - Main value
- `subtitle?: string` - Optional subtitle
- `icon?: LucideIcon` - Optional icon
- `trend?: { value: number; direction: 'up' | 'down' }` - Optional trend
- `color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'` - Color variant

**Features:**
- 5 color variants with semantic meanings
- Trend indicator with percentage and arrow
- Framer Motion animation (fade + slide up)
- Icon support (Lucide icons)
- Responsive layout

#### **ChartCard** - Chart Wrapper

Wrapper component for all chart types:

```tsx
import { ChartCard, LineChartWidget } from '@/components/visual_analytics';

<ChartCard
  title="Activity Timeline"
  description="Jobs created over time"
  actions={<DateRangeFilter value={days} onChange={setDays} />}
>
  <LineChartWidget data={timeline} height={300} />
</ChartCard>
```

**Props:**
- `title: string` - Chart title
- `description?: string` - Optional description
- `children: ReactNode` - Chart component
- `actions?: ReactNode` - Optional actions slot (filters, buttons)

#### **States** - Loading/Error/Empty

State components for better UX:

```tsx
import {
  LoadingSkeleton,
  LoadingState,
  ErrorState,
  EmptyState,
  NoPermissionState
} from '@/components/visual_analytics';

// While fetching data
if (isLoading) return <LoadingState message="Loading analytics..." />;

// On error
if (error) return <ErrorState message={error.message} onRetry={refetch} />;

// No data
if (!data || data.total_clips === 0) {
  return <EmptyState message="No clips found" />;
}

// No permission
if (error?.status === 403) {
  return <NoPermissionState />;
}
```

**Components:**
- `LoadingSkeleton` - Pulse animation placeholder
- `LoadingState` - Spinner with message
- `ErrorState` - Error display with retry button
- `EmptyState` - No data message with optional action
- `NoPermissionState` - RBAC access denied message

#### **LineChartWidget** - Line Chart

Recharts line chart with multi-series support:

```tsx
import { LineChartWidget } from '@/components/visual_analytics';
import type { Timeseries } from '@/lib/visual_analytics/types';

const data: Timeseries[] = [
  { timestamp: '2024-01-01T00:00:00Z', value: 10, series: 'clips' },
  { timestamp: '2024-01-02T00:00:00Z', value: 15, series: 'clips' },
];

<LineChartWidget
  data={data}
  height={350}
  showLegend={true}
  showGrid={true}
/>
```

**Props:**
- `data: Timeseries[]` - Array of time series points
- `height?: number` - Chart height (default: 300)
- `showLegend?: boolean` - Show legend (default: true)
- `showGrid?: boolean` - Show grid (default: true)

**Features:**
- Multi-series support (different colors per series)
- Date formatting with date-fns
- Responsive container
- CartesianGrid, Tooltip, Legend
- Custom colors: `#8b5cf6`, `#3b82f6`, `#10b981`, `#f59e0b`, `#ef4444`

#### **BarChartWidget** - Bar Chart

Recharts bar chart for distributions:

```tsx
import { BarChartWidget } from '@/components/visual_analytics';

const data = [
  { name: 'Instagram', value: 120, color: '#E4405F' },
  { name: 'TikTok', value: 98, color: '#000000' },
  { name: 'YouTube', value: 45, color: '#FF0000' },
];

<BarChartWidget
  data={data}
  height={300}
  showLegend={false}
  color="#8b5cf6"
/>
```

**Props:**
- `data: BarChartData[]` - Array of bars `{ name, value, color? }`
- `height?: number` - Chart height
- `showLegend?: boolean` - Show legend
- `color?: string` - Default bar color (if not per-bar)

**Features:**
- Custom colors per bar (or default color)
- Rounded corners (radius `[8,8,0,0]`)
- Responsive container
- Grid toggle

#### **PieChartWidget** - Pie/Donut Chart

Recharts pie chart with donut mode:

```tsx
import { PieChartWidget } from '@/components/visual_analytics';

const data = [
  { name: 'Instagram', value: 60 },
  { name: 'TikTok', value: 30 },
  { name: 'YouTube', value: 10 },
];

<PieChartWidget
  data={data}
  height={300}
  showLegend={true}
  innerRadius={60} // Donut mode
/>
```

**Props:**
- `data: PieChartData[]` - Array of slices `{ name, value }`
- `height?: number` - Chart height
- `showLegend?: boolean` - Show legend
- `innerRadius?: number` - Donut inner radius (0 for pie)

**Features:**
- Auto color assignment (6 colors)
- Percentage labels on slices
- Responsive container
- Donut mode support

#### **PlatformsBreakdownCard**

Platform performance display with pie chart + metrics list:

```tsx
import { PlatformsBreakdownCard } from '@/components/visual_analytics';

<PlatformsBreakdownCard data={platformStats} />
```

**Features:**
- Pie chart showing distribution
- Metrics list with platform icons
- Platform-specific colors (Instagram: #E4405F, TikTok: #000000, YouTube: #FF0000)
- Best platform badge
- Clips and publications count per platform

#### **ClipRankingsTable**

Top clips table with ranking and scores:

```tsx
import { ClipRankingsTable } from '@/components/visual_analytics';

<ClipRankingsTable data={rankings} maxRows={10} />
```

**Props:**
- `data: ClipRanking[]` - Array of top clips
- `maxRows?: number` - Max rows to display (default: 10)

**Features:**
- Trophy icon for #1 clip
- Duration formatter (MM:SS)
- Score progress bars (0-100)
- Clip ID truncation
- Responsive table layout

#### **OverviewGrid**

8-card stats grid for overview page:

```tsx
import { OverviewGrid } from '@/components/visual_analytics';

<OverviewGrid data={overview} />
```

**Features:**
- Displays 8 key metrics:
  * Total clips (blue)
  * Total jobs (purple)
  * Total publications (green)
  * Total campaigns (yellow)
  * Clips per week (blue)
  * Clips per month (purple)
  * Average clip score (green)
  * Top clips count (yellow)
- Responsive grid (1 col mobile, 2 cols tablet, 4 cols desktop)
- Icons for each metric (Lucide icons)
- Color coding per category

#### **DateRangeFilter**

Time range selector with presets:

```tsx
import { DateRangeFilter } from '@/components/visual_analytics';

<DateRangeFilter
  value={days}
  onChange={setDays}
  disabled={isLoading}
/>
```

**Props:**
- `value: number` - Selected days (7, 14, 30, etc.)
- `onChange: (days: number) => void` - Change handler
- `disabled?: boolean` - Disabled state

**Features:**
- 7 presets: 7, 14, 30, 60, 90, 180, 365 days
- Shadcn Select component
- Calendar icon
- Responsive design

---

### Page Layer

#### **/dashboard/visual/overview** - Complete Overview

Main analytics dashboard with comprehensive metrics:

```tsx
// app/dashboard/visual/overview/page.tsx
'use client';

import { useState } from 'react';
import { useOverviewAnalytics } from '@/lib/visual_analytics/hooks';
import {
  DateRangeFilter,
  OverviewGrid,
  ChartCard,
  ClipRankingsTable,
  LoadingState,
  ErrorState,
  EmptyState,
} from '@/components/visual_analytics';

export default function OverviewPage() {
  const [days, setDays] = useState(30);
  const { data, isLoading, error, refetch } = useOverviewAnalytics({ days });

  if (isLoading) return <LoadingState message="Loading overview..." />;
  if (error) return <ErrorState message={error.message} onRetry={refetch} />;
  if (!data) return <EmptyState message="No data available" />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Analytics Overview</h1>
        <DateRangeFilter value={days} onChange={setDays} />
      </div>

      <OverviewGrid data={data} />

      <ChartCard title="Correlations">
        {/* Correlation metrics */}
      </ChartCard>

      <ChartCard title="Top Clips">
        <ClipRankingsTable data={data.top_clips} />
      </ChartCard>
    </div>
  );
}
```

**Features:**
- Complete analytics overview
- 8 summary stats (OverviewGrid)
- Correlations card
- Rule engine metrics card
- Top 10 clips table
- DateRangeFilter (30 days default)
- Generated at timestamp
- Full error/loading/empty states

#### **/dashboard/visual/platforms** - Platform Performance

Platform comparison and performance metrics:

**Features:**
- 3 summary stat cards (total platforms, best platform, avg clips)
- PlatformsBreakdownCard (pie chart + list)
- 2 bar charts:
  * Clips by platform
  * Publications by platform
- DateRangeFilter
- Platform-specific colors and icons

#### **/dashboard/visual/clips** - Clips Distribution

Clips analytics and distribution:

**Features:**
- 3 summary stats (total clips, avg score, avg duration)
- Duration histogram (BarChart)
- Score histogram (BarChart)
- ClipRankingsTable (top 10)
- DateRangeFilter
- Empty state when total_clips = 0

#### **/dashboard/visual/timeline** - Activity Timeline

Activity over time visualization:

**Features:**
- 4 timeline charts:
  * Jobs created over time
  * Publications over time
  * Clips created over time
  * Orchestrator jobs over time
- LineChartWidget for each
- Individual empty state per chart
- DateRangeFilter (7 days default)
- Date range display

#### **/dashboard/visual/campaigns** - Campaign Metrics

Campaign performance and metrics:

**Features:**
- 3 summary stats (total campaigns, active campaigns, avg clips per campaign)
- 2 bar charts:
  * Clips by campaign
  * Publications by campaign
- Full campaigns table:
  * Campaign name
  * Status badge (active/inactive)
  * Clips count
  * Publications count
  * Average score
  * Created date
- DateRangeFilter
- Date formatting with date-fns
- Empty state when total_campaigns = 0

#### **/dashboard/visual/heatmap** - Activity Heatmap

Hour x Day activity heatmap:

**Features:**
- Metric selector (clips, jobs, publications)
- HeatmapWidget with custom grid
- Color scale (viridis)
- 24h x 7d matrix
- DateRangeFilter
- Peak activity indicator

#### **/dashboard/visual** - Main Page

Redirect page to overview:

```tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LoadingState } from '@/components/visual_analytics';

export default function VisualAnalyticsPage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/dashboard/visual/overview');
  }, [router]);

  return <LoadingState message="Loading..." />;
}
```

---

## 🧪 Testing

### Test Structure

```
dashboard/__tests__/
├── lib/visual_analytics/
│   ├── api.test.ts              # API client tests
│   └── hooks.test.ts            # React Query hooks tests
├── components/visual_analytics/
│   ├── StatCard.test.tsx        # StatCard tests
│   ├── ChartCard.test.tsx       # ChartCard tests
│   ├── States.test.tsx          # States tests
│   ├── LineChartWidget.test.tsx # LineChartWidget tests
│   ├── BarChartWidget.test.tsx  # BarChartWidget tests
│   └── PieChartWidget.test.tsx  # PieChartWidget tests
└── app/dashboard/visual/
    ├── overview.test.tsx        # Overview page tests
    ├── platforms.test.tsx       # Platforms page tests
    └── clips.test.tsx           # Clips page tests
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test hooks.test.ts
```

### Example Tests

#### API Client Tests

```typescript
// dashboard/__tests__/lib/visual_analytics/api.test.ts
import { visualAnalyticsApi } from '@/lib/visual_analytics/api';

describe('visualAnalyticsApi', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
    localStorage.setItem('auth_token', 'test-token');
  });

  it('should fetch overview with auth token', async () => {
    const mockData = { total_clips: 100 };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const result = await visualAnalyticsApi.getOverview({ days: 30 });
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('days=30'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    );
    expect(result).toEqual(mockData);
  });

  it('should throw on HTTP error', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    await expect(
      visualAnalyticsApi.getOverview()
    ).rejects.toThrow('HTTP 500');
  });
});
```

#### Hook Tests

```typescript
// dashboard/__tests__/lib/visual_analytics/hooks.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useOverviewAnalytics } from '@/lib/visual_analytics/hooks';
import { visualAnalyticsApi } from '@/lib/visual_analytics/api';

jest.mock('@/lib/visual_analytics/api');

describe('useOverviewAnalytics', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('should fetch overview data', async () => {
    const mockData = { total_clips: 100 };
    (visualAnalyticsApi.getOverview as jest.Mock).mockResolvedValue(mockData);

    const { result } = renderHook(() => useOverviewAnalytics({ days: 30 }), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockData);
    expect(visualAnalyticsApi.getOverview).toHaveBeenCalledWith({ days: 30 });
  });

  it('should handle errors', async () => {
    const error = new Error('Network error');
    (visualAnalyticsApi.getOverview as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useOverviewAnalytics(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toEqual(error);
  });
});
```

#### Component Tests

```typescript
// dashboard/__tests__/components/visual_analytics/StatCard.test.tsx
import { render, screen } from '@testing-library/react';
import { StatCard } from '@/components/visual_analytics';
import { Video } from 'lucide-react';

describe('StatCard', () => {
  it('should render title and value', () => {
    render(<StatCard title="Total Clips" value={1234} />);

    expect(screen.getByText('Total Clips')).toBeInTheDocument();
    expect(screen.getByText('1234')).toBeInTheDocument();
  });

  it('should render with icon', () => {
    render(<StatCard title="Clips" value={100} icon={Video} />);

    const icon = screen.getByRole('img', { hidden: true });
    expect(icon).toBeInTheDocument();
  });

  it('should render trend indicator', () => {
    render(
      <StatCard
        title="Clips"
        value={100}
        trend={{ value: 12.5, direction: 'up' }}
      />
    );

    expect(screen.getByText('+12.5%')).toBeInTheDocument();
  });

  it('should apply color variant', () => {
    const { container } = render(
      <StatCard title="Clips" value={100} color="green" />
    );

    expect(container.querySelector('.text-green-600')).toBeInTheDocument();
  });
});
```

---

## 🚀 Usage Guide

### Installation

```bash
# Install dependencies
cd dashboard
npm install
```

### Development

```bash
# Run development server
npm run dev

# Open browser
open http://localhost:3000/dashboard/visual
```

### Environment Variables

Create `.env.local` in dashboard root:

```env
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Optional: Enable React Query DevTools
NEXT_PUBLIC_ENABLE_QUERY_DEVTOOLS=true
```

### Authentication

The API client expects an auth token in localStorage:

```typescript
// Login and store token
localStorage.setItem('auth_token', 'your-jwt-token');

// The API client will automatically use it
const data = await visualAnalyticsApi.getOverview();

// Logout
localStorage.removeItem('auth_token');
```

### Basic Usage Example

```tsx
'use client';

import { useState } from 'react';
import { useOverviewAnalytics } from '@/lib/visual_analytics/hooks';
import {
  DateRangeFilter,
  StatCard,
  ChartCard,
  LineChartWidget,
  LoadingState,
  ErrorState,
} from '@/components/visual_analytics';

export default function MyAnalyticsPage() {
  const [days, setDays] = useState(30);
  const { data, isLoading, error } = useOverviewAnalytics({ days });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message={error.message} />;

  return (
    <div className="space-y-6">
      <DateRangeFilter value={days} onChange={setDays} />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Total Clips" value={data.total_clips} />
        <StatCard title="Total Jobs" value={data.total_jobs} />
        <StatCard title="Avg Score" value={data.average_clip_score} />
      </div>

      <ChartCard title="Clips Timeline">
        <LineChartWidget data={data.clips_timeline} />
      </ChartCard>
    </div>
  );
}
```

### Advanced: Custom Hooks

Create custom analytics hooks for specific needs:

```typescript
// lib/visual_analytics/custom-hooks.ts
import { useMemo } from 'react';
import { useOverviewAnalytics, usePlatformAnalytics } from './hooks';

// Combined hook with derived data
export function useCombinedAnalytics(days: number) {
  const overview = useOverviewAnalytics({ days });
  const platforms = usePlatformAnalytics({ days });

  const combinedData = useMemo(() => {
    if (!overview.data || !platforms.data) return null;

    return {
      totalMetrics: {
        clips: overview.data.total_clips,
        jobs: overview.data.total_jobs,
        publications: overview.data.total_publications,
      },
      platformBreakdown: platforms.data.platforms,
      topClips: overview.data.top_clips,
    };
  }, [overview.data, platforms.data]);

  return {
    data: combinedData,
    isLoading: overview.isLoading || platforms.isLoading,
    error: overview.error || platforms.error,
  };
}
```

---

## 🎨 Styling & Theming

### Dark Mode

All components support dark mode via Tailwind CSS:

```tsx
// Dark mode is automatic with Tailwind's dark: prefix
<div className="bg-white dark:bg-gray-800">
  <h1 className="text-gray-900 dark:text-white">Title</h1>
</div>
```

### Custom Colors

Modify Tailwind config for custom color scheme:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          // ... more shades
          900: '#0c4a6e',
        },
      },
    },
  },
};
```

### Component Variants

StatCard supports 5 color variants:

```tsx
<StatCard color="blue" />   // Default, neutral metrics
<StatCard color="green" />  // Positive metrics (success rate)
<StatCard color="yellow" /> // Warning metrics (pending jobs)
<StatCard color="red" />    // Error metrics (failed jobs)
<StatCard color="purple" /> // Special metrics (AI-related)
```

---

## 📊 Chart Customization

### Line Chart Customization

```tsx
<LineChartWidget
  data={timeline}
  height={400}
  showLegend={true}
  showGrid={true}
  // Custom colors per series
  colors={{
    clips: '#8b5cf6',
    jobs: '#3b82f6',
    publications: '#10b981',
  }}
/>
```

### Bar Chart with Custom Colors

```tsx
const data = [
  { name: 'Instagram', value: 120, color: '#E4405F' },
  { name: 'TikTok', value: 98, color: '#000000' },
  { name: 'YouTube', value: 45, color: '#FF0000' },
];

<BarChartWidget data={data} height={300} />
```

### Pie Chart as Donut

```tsx
<PieChartWidget
  data={platformData}
  innerRadius={60} // Donut mode
  height={300}
/>
```

---

## 🔐 RBAC Integration

### Permission Checking

```tsx
import { useAuth } from '@/lib/auth'; // Your auth hook
import { NoPermissionState } from '@/components/visual_analytics';

export default function ProtectedPage() {
  const { user } = useAuth();

  // Check permission
  if (!user?.permissions?.includes('view_analytics')) {
    return <NoPermissionState />;
  }

  // Render analytics
  return <AnalyticsDashboard />;
}
```

### Role-Based Pages

```tsx
// Middleware or page-level check
export default function AdminAnalyticsPage() {
  const { user } = useAuth();

  if (user?.role !== 'admin') {
    return <NoPermissionState message="Admin access required" />;
  }

  // Admin-only analytics
  return <AdvancedAnalytics />;
}
```

---

## 🐛 Debugging

### React Query DevTools

Enable in development:

```tsx
// app/layout.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

### API Error Logging

```typescript
// lib/visual_analytics/api.ts
async function fetchWithAuth(url: string): Promise<any> {
  try {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(url, {
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('API Error:', error);
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}
```

### Component Error Boundaries

```tsx
'use client';

import { Component, ReactNode } from 'react';
import { ErrorState } from '@/components/visual_analytics';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class AnalyticsErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorState
          message={this.state.error?.message || 'Something went wrong'}
          onRetry={() => this.setState({ hasError: false })}
        />
      );
    }

    return this.props.children;
  }
}
```

---

## 🚀 Performance Optimization

### Prefetching

```tsx
import { usePrefetchAnalytics } from '@/lib/visual_analytics/hooks';

export default function DashboardNav() {
  const prefetch = usePrefetchAnalytics();

  return (
    <nav>
      <Link
        href="/dashboard/visual/overview"
        onMouseEnter={() => prefetch({ days: 30 })}
      >
        Overview
      </Link>
    </nav>
  );
}
```

### Lazy Loading

```tsx
import dynamic from 'next/dynamic';

// Lazy load heavy chart components
const LineChartWidget = dynamic(
  () => import('@/components/visual_analytics').then(m => m.LineChartWidget),
  { loading: () => <LoadingSkeleton /> }
);
```

### Memoization

```tsx
import { useMemo } from 'react';

export function ClipRankingsTable({ data }) {
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => b.score - a.score);
  }, [data]);

  return <table>{/* render sortedData */}</table>;
}
```

---

## 📱 Responsive Design

All components are responsive by default:

```tsx
// Grid layout - responsive breakpoints
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  <StatCard />
  <StatCard />
  <StatCard />
  <StatCard />
</div>

// Charts - responsive container (Recharts)
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    {/* ... */}
  </LineChart>
</ResponsiveContainer>
```

**Breakpoints:**
- Mobile: < 768px (1 column)
- Tablet: 768px - 1024px (2 columns)
- Desktop: > 1024px (4 columns)

---

## 🔄 Roadmap

### Completed ✅
- [x] TypeScript types library
- [x] API client with authentication
- [x] React Query hooks with caching
- [x] 13 reusable components
- [x] 7 page components
- [x] Dark mode support
- [x] Responsive design
- [x] RBAC integration
- [x] Error/loading/empty states
- [x] Comprehensive tests (20+)

### Planned 🎯
- [ ] Export functionality (CSV, PNG)
- [ ] Custom date range picker
- [ ] Advanced filters (platform, campaign, etc.)
- [ ] Real-time updates (WebSocket)
- [ ] Comparison mode (compare time periods)
- [ ] Saved dashboards (user preferences)
- [ ] Annotations on charts
- [ ] Share analytics reports
- [ ] Email notifications for thresholds
- [ ] Mobile app (React Native)

### Future Ideas 💡
- [ ] AI-powered insights and predictions
- [ ] Custom metric builder
- [ ] Drill-down analytics (click chart → details)
- [ ] A/B test analytics
- [ ] Cost analytics (compute costs per job)
- [ ] Performance benchmarking
- [ ] Multi-tenant support
- [ ] White-label customization

---

## 🤝 Contributing

### Development Workflow

1. **Create branch:**
   ```bash
   git checkout -b feature/new-chart-type
   ```

2. **Make changes:**
   - Add components in `components/visual_analytics/`
   - Add types in `lib/visual_analytics/types.ts`
   - Add tests in `__tests__/`

3. **Test changes:**
   ```bash
   npm test
   npm run build
   ```

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat: Add new chart type for X"
   git push origin feature/new-chart-type
   ```

5. **Create PR and merge**

### Code Style

- Use TypeScript strict mode
- Follow ESLint rules (`npm run lint`)
- Use Prettier for formatting (`npm run format`)
- Write tests for new components
- Document props with JSDoc comments
- Use semantic commit messages (feat, fix, docs, etc.)

---

## 📝 License

Copyright © 2024. All rights reserved.

---

## 📞 Support

For issues or questions:

- **GitHub Issues:** [Create issue](https://github.com/your-repo/issues)
- **Documentation:** This README
- **Backend API Docs:** `README_VISUAL_ANALYTICS_BACKEND.md`

---

**Last Updated:** 2024-01-XX  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
