'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts';
import { fetchProvinceComparison } from '@/lib/api';
import { useFilterStore } from '@/stores/filterStore';
import { FadeIn } from '@/components/ui/FadeIn';

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

export function ProvinceComparison() {
  const yearRange = useFilterStore((s) => s.yearRange);
  const { data, isLoading } = useQuery({
    queryKey: ['province-comparison', yearRange[1]],
    queryFn: () => fetchProvinceComparison(yearRange[1]),
  });

  const chartData = React.useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.map((item) => ({
      name: item.province,
      count: item.count,
    }));
  }, [data]);

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <h3 className="text-sm font-semibold text-[#F8FAFC] mb-4">
        Province Comparison
      </h3>
      <div className="h-48 sm:h-64">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="w-full h-full flex items-end gap-2 px-8">
              {[60, 80, 45, 70, 55].map((h, i) => (
                <div key={i} className="skeleton flex-1 rounded-t" style={{ height: `${h}%` }} />
              ))}
            </div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-[#94A3B8]">No province data available</p>
          </div>
        ) : (
          <FadeIn className="h-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis
                type="number"
                stroke="#94A3B8"
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
                tickFormatter={(val: number) => val >= 1000 ? `${(val / 1000).toFixed(0)}k` : String(val)}
              />
              <YAxis
                type="category"
                dataKey="name"
                stroke="#94A3B8"
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
                width={60}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(51, 65, 85, 0.3)' }} />
              <Bar
                dataKey="count"
                radius={[0, 4, 4, 0]}
                fill="#06B6D4"
              />
            </BarChart>
          </ResponsiveContainer>
          </FadeIn>
        )}
      </div>
    </div>
  );
}
