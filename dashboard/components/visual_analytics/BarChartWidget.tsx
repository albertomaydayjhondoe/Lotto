/**
 * BarChartWidget Component (PASO 8.4)
 * 
 * Reusable bar chart using Recharts
 */

'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

export interface BarChartData {
  name: string;
  value: number;
  color?: string;
}

export interface BarChartWidgetProps {
  data: BarChartData[];
  height?: number;
  showLegend?: boolean;
  showGrid?: boolean;
  color?: string;
}

export function BarChartWidget({
  data,
  height = 300,
  showLegend = false,
  showGrid = true,
  color = '#3b82f6',
}: BarChartWidgetProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
        <XAxis
          dataKey="name"
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
        <Bar dataKey="value" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color || color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
