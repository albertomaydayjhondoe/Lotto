/**
 * DateRangeFilter Component (PASO 8.4)
 * 
 * Filter for selecting time range
 */

'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from 'lucide-react';

export interface DateRangeFilterProps {
  value: number;
  onChange: (days: number) => void;
  disabled?: boolean;
}

const timeRanges = [
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 14 days', value: 14 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last 60 days', value: 60 },
  { label: 'Last 90 days', value: 90 },
  { label: 'Last 180 days', value: 180 },
  { label: 'Last year', value: 365 },
];

export function DateRangeFilter({ value, onChange, disabled }: DateRangeFilterProps) {
  return (
    <div className="flex items-center gap-2">
      <Calendar className="h-4 w-4 text-muted-foreground" />
      <Select
        value={value.toString()}
        onValueChange={(v) => onChange(parseInt(v, 10))}
        disabled={disabled}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select time range" />
        </SelectTrigger>
        <SelectContent>
          {timeRanges.map((range) => (
            <SelectItem key={range.value} value={range.value.toString()}>
              {range.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
