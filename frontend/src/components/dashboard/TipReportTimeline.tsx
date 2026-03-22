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
  Legend,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts';
import { Loader2, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import { fetchTipReportDetails } from '@/lib/api';

const TIER_COLORS: Record<string, string> = {
  'Tier 1': 'bg-[#10B981]/10 text-[#10B981]',
  'Tier 2': 'bg-[#F59E0B]/10 text-[#F59E0B]',
  'Tier 2 Watch List': 'bg-[#EF4444]/10 text-[#EF4444]',
  'Tier 3': 'bg-[#EF4444]/10 text-[#EF4444]',
};

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-[#334155] bg-[#1E293B] px-3 py-2 shadow-xl">
      <p className="text-xs text-[#94A3B8] mb-1">Year: {label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value?.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

export function TipReportTimeline() {
  const { data, isLoading } = useQuery({
    queryKey: ['tip-details'],
    queryFn: fetchTipReportDetails,
  });

  const chartData = React.useMemo(() => {
    if (!data) return [];
    return data.map((row) => ({
      year: row.year,
      investigations: row.investigations ?? 0,
      prosecutions: row.prosecutions ?? 0,
      convictions: row.convictions ?? 0,
      victimsIdentified: row.victimsIdentified ?? 0,
    }));
  }, [data]);

  const latestReport = data && data.length > 0 ? data[data.length - 1] : null;

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 lg:col-span-2">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-[#EC4899]" />
          <h3 className="text-sm font-semibold text-[#F8FAFC]">
            TIP Report — Investigation Funnel
          </h3>
        </div>
        {latestReport?.tierRanking && (
          <span
            className={cn(
              'rounded-full px-2.5 py-0.5 text-xs font-medium',
              TIER_COLORS[latestReport.tierRanking] ?? 'bg-[#334155] text-[#94A3B8]',
            )}
          >
            {latestReport.tierRanking} ({latestReport.year})
          </span>
        )}
      </div>

      <div className="h-48 sm:h-64">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-[#94A3B8]">No TIP report data available</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="year" stroke="#94A3B8" tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <YAxis stroke="#94A3B8" tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94A3B8' }} />
              <Bar dataKey="investigations" name="Investigations" fill="#06B6D4" radius={[2, 2, 0, 0]} />
              <Bar dataKey="prosecutions" name="Prosecutions" fill="#F59E0B" radius={[2, 2, 0, 0]} />
              <Bar dataKey="convictions" name="Convictions" fill="#10B981" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Key findings */}
      {latestReport?.keyFindings && (
        <div className="mt-4 rounded-md bg-[#0F172A] px-3 py-2">
          <p className="text-xs text-[#94A3B8] mb-1">Key Findings ({latestReport.year})</p>
          <p className="text-xs text-[#F8FAFC] line-clamp-3">{latestReport.keyFindings}</p>
        </div>
      )}
    </div>
  );
}
