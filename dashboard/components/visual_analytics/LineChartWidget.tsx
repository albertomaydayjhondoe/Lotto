/**
 * LineChartWidget Component (PASO 8.4)
 * 
 * Reusable line chart using Recharts
 */

'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';
import type { Timeseries } from '@/lib/visual_analytics/types';

export interface LineChartWidgetProps {
  data: Timeseries[];
  height?: number;
  showLegend?: boolean;
  showGrid?: boolean;
}

export function LineChartWidget({
  data,
  height = 300,
  showLegend = true,
  showGrid = true,
}: LineChartWidgetProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No data available
      </div>
    );
  }

  // Transform data for Recharts
  const chartData: any[] = [];
  const seriesNames = data.map(s => s.series_name);
  
  // Get all unique timestamps
  const allTimestamps = new Set<string>();
  data.forEach(series => {
    series.data.forEach(point => {
      allTimestamps.add(point.timestamp);
    });
  });
  
  // Create data points for each timestamp
  Array.from(allTimestamps).sort().forEach(timestamp => {
    const dataPoint: any = {
      timestamp,
      formattedTime: format(new Date(timestamp), 'MMM dd HH:mm'),
    };
    
    data.forEach(series => {
      const point = series.data.find(p => p.timestamp === timestamp);
      dataPoint[series.series_name] = point?.value ?? null;
    });
    
    chartData.push(dataPoint);
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
        <XAxis
          dataKey="formattedTime"
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
          }}
        />
        {showLegend && <Legend />}
        {data.map((series, index) => (
          <Line
            key={series.series_name}
            type="monotone"
            dataKey={series.series_name}
            stroke={series.color || `hsl(${index * 60}, 70%, 50%)`}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
