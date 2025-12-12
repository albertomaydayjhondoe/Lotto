/**
 * @jest-environment jsdom
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LineChartWidget } from '@/components/visual_analytics';
import type { Timeseries } from '@/lib/visual_analytics/types';

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  LineChart: ({ children }: any) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: ({ dataKey }: any) => <div data-testid={`line-${dataKey}`} />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}));

describe('LineChartWidget', () => {
  const mockData: Timeseries[] = [
    {
      timestamp: '2024-01-01T00:00:00Z',
      value: 10,
      series: 'clips',
    },
    {
      timestamp: '2024-01-02T00:00:00Z',
      value: 15,
      series: 'clips',
    },
    {
      timestamp: '2024-01-03T00:00:00Z',
      value: 12,
      series: 'clips',
    },
  ];

  it('should render LineChart component', () => {
    render(<LineChartWidget data={mockData} />);

    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('should render CartesianGrid when showGrid is true', () => {
    render(<LineChartWidget data={mockData} showGrid={true} />);

    expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument();
  });

  it('should not render CartesianGrid when showGrid is false', () => {
    render(<LineChartWidget data={mockData} showGrid={false} />);

    expect(screen.queryByTestId('cartesian-grid')).not.toBeInTheDocument();
  });

  it('should render Legend when showLegend is true', () => {
    render(<LineChartWidget data={mockData} showLegend={true} />);

    expect(screen.getByTestId('legend')).toBeInTheDocument();
  });

  it('should not render Legend when showLegend is false', () => {
    render(<LineChartWidget data={mockData} showLegend={false} />);

    expect(screen.queryByTestId('legend')).not.toBeInTheDocument();
  });

  it('should render XAxis and YAxis', () => {
    render(<LineChartWidget data={mockData} />);

    expect(screen.getByTestId('x-axis')).toBeInTheDocument();
    expect(screen.getByTestId('y-axis')).toBeInTheDocument();
  });

  it('should render Tooltip', () => {
    render(<LineChartWidget data={mockData} />);

    expect(screen.getByTestId('tooltip')).toBeInTheDocument();
  });

  it('should handle empty data', () => {
    render(<LineChartWidget data={[]} />);

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('should render with custom height', () => {
    const { container } = render(<LineChartWidget data={mockData} height={400} />);

    const responsiveContainer = screen.getByTestId('responsive-container');
    expect(responsiveContainer).toBeInTheDocument();
  });

  it('should render multiple series', () => {
    const multiSeriesData: Timeseries[] = [
      { timestamp: '2024-01-01T00:00:00Z', value: 10, series: 'clips' },
      { timestamp: '2024-01-01T00:00:00Z', value: 5, series: 'jobs' },
      { timestamp: '2024-01-02T00:00:00Z', value: 15, series: 'clips' },
      { timestamp: '2024-01-02T00:00:00Z', value: 8, series: 'jobs' },
    ];

    render(<LineChartWidget data={multiSeriesData} />);

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('should handle data with missing series field', () => {
    const dataWithoutSeries: Timeseries[] = [
      { timestamp: '2024-01-01T00:00:00Z', value: 10 },
      { timestamp: '2024-01-02T00:00:00Z', value: 15 },
    ];

    render(<LineChartWidget data={dataWithoutSeries} />);

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });
});
