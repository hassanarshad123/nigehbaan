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
  Legend,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import { fetchConvictionRates } from '@/lib/api';

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="rounded-md border border-[#334155] bg-[#1E293B] px-3 py-2 shadow-xl">
      <p className="text-xs text-[#94A3B8] mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value}%
        </p>
      ))}
    </div>
  );
}

export function ConvictionRates() {
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['conviction-rates'],
    queryFn: () => fetchConvictionRates(),
  });

  const chartData = React.useMemo(() => {
    if (!rawData || rawData.length === 0) return [];
    return rawData.map((row) => ({
      year: row.year,
      prosecutionRate: row.investigations > 0
        ? Math.round((row.prosecutions / row.investigations) * 1000) / 10
        : 0,
      convictionRate: row.rate,
    }));
  }, [rawData]);

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <h3 className="text-sm font-semibold text-[#F8FAFC] mb-4">
        Prosecution vs. Conviction Rates
      </h3>
      <div className="h-48 sm:h-64">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-[#94A3B8]">No conviction rate data available</p>
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
                tickFormatter={(val: number) => `${val}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: '11px', color: '#94A3B8' }}
              />
              <Line
                type="monotone"
                dataKey="prosecutionRate"
                name="Prosecution Rate"
                stroke="#F59E0B"
                strokeWidth={2}
                dot={{ r: 3, fill: '#F59E0B', stroke: '#0F172A', strokeWidth: 2 }}
              />
              <Line
                type="monotone"
                dataKey="convictionRate"
                name="Conviction Rate"
                stroke="#10B981"
                strokeWidth={2}
                dot={{ r: 3, fill: '#10B981', stroke: '#0F172A', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
