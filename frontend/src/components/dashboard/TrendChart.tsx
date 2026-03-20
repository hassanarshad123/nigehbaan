'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import { fetchTrendData } from '@/lib/api';

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="rounded-md border border-[#334155] bg-[#1E293B] px-3 py-2 shadow-xl">
      <p className="text-xs text-[#94A3B8] mb-0.5">{label}</p>
      <p className="text-sm font-semibold text-[#F8FAFC]">
        {payload[0].value?.toLocaleString()} incidents
      </p>
    </div>
  );
}

export function TrendChart() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: () => fetchTrendData(),
  });

  // Aggregate by year (backend may return multiple source rows per year)
  const chartData = React.useMemo(() => {
    if (!data || data.length === 0) return [];
    const byYear = new Map<number, number>();
    for (const row of data) {
      byYear.set(row.year, (byYear.get(row.year) ?? 0) + row.count);
    }
    return Array.from(byYear.entries())
      .map(([year, count]) => ({ year, count }))
      .sort((a, b) => a.year - b.year);
  }, [data]);

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <h3 className="text-sm font-semibold text-[#F8FAFC] mb-4">Incident Trend</h3>
      <div className="h-64">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-[#94A3B8]">No trend data available</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="year"
                stroke="#94A3B8"
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
              />
              <YAxis
                stroke="#94A3B8"
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
                tickFormatter={(val: number) => `${(val / 1000).toFixed(1)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#06B6D4"
                strokeWidth={2}
                dot={{ r: 3, fill: '#06B6D4', stroke: '#0F172A', strokeWidth: 2 }}
                activeDot={{ r: 5, fill: '#06B6D4' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
