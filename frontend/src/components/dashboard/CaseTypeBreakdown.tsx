'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
} from 'recharts';
import { fetchCaseTypes } from '@/lib/api';
import { useFilterStore } from '@/stores/filterStore';
import { FadeIn } from '@/components/ui/FadeIn';

interface CaseTypeData {
  name: string;
  value: number;
  color: string;
}

const COLORS = [
  '#EF4444', '#DC2626', '#F97316', '#F59E0B', '#EC4899',
  '#BE185D', '#D946EF', '#8B5CF6', '#6366F1', '#991B1B',
  '#06B6D4', '#94A3B8',
];

function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;

  const entry = payload[0];
  return (
    <div className="rounded-md border border-[#334155] bg-[#1E293B] px-3 py-2 shadow-xl">
      <p className="text-xs text-[#94A3B8] mb-0.5">{entry.name}</p>
      <p className="text-sm font-semibold text-[#F8FAFC]">
        {entry.value?.toLocaleString()} incidents
      </p>
    </div>
  );
}

export function CaseTypeBreakdown() {
  const selectedProvince = useFilterStore((s) => s.selectedProvince);
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['case-types', selectedProvince],
    queryFn: () => fetchCaseTypes(selectedProvince ?? undefined),
  });

  const chartData: CaseTypeData[] = React.useMemo(() => {
    if (!rawData || rawData.length === 0) return [];
    return rawData.map((item, idx) => ({
      name: item.type,
      value: item.count,
      color: COLORS[idx % COLORS.length],
    }));
  }, [rawData]);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
        <h3 className="text-sm font-semibold text-[#F8FAFC] mb-4">Case Type Breakdown</h3>
        <div className="flex flex-col items-center gap-4 sm:flex-row">
          <div className="skeleton h-32 w-32 sm:h-40 sm:w-40 shrink-0 rounded-full" />
          <div className="space-y-2 flex-1 w-full">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="skeleton h-2.5 w-2.5 rounded-sm shrink-0" />
                <div className="skeleton h-3 flex-1" />
                <div className="skeleton h-3 w-10" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
        <h3 className="text-sm font-semibold text-[#F8FAFC] mb-4">Case Type Breakdown</h3>
        <div className="flex h-52 items-center justify-center">
          <p className="text-sm text-[#94A3B8]">No case type data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <h3 className="text-sm font-semibold text-[#F8FAFC] mb-4">
        Case Type Breakdown
      </h3>

      <FadeIn>
      <div className="flex flex-col items-center gap-4 sm:flex-row">
        {/* Donut chart */}
        <div className="h-32 w-32 shrink-0 sm:h-52 sm:w-52">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} stroke="#1E293B" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="space-y-2 flex-1">
          {chartData.map((entry) => (
            <div key={entry.name} className="flex items-center gap-2 text-xs">
              <span
                className="inline-block h-2.5 w-2.5 rounded-sm shrink-0"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-[#F8FAFC] flex-1">{entry.name}</span>
              <span className="text-[#94A3B8] tabular-nums">
                {entry.value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
      </FadeIn>
    </div>
  );
}
