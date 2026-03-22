'use client';

import React, { useState } from 'react';
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
import { Loader2, Database } from 'lucide-react';
import { fetchStatisticalReports } from '@/lib/api';

const SOURCE_OPTIONS = [
  { value: '', label: 'All Sources' },
  { value: 'sahil', label: 'Sahil' },
  { value: 'sparc', label: 'SPARC' },
  { value: 'dol_child_labor', label: 'DOL Child Labor' },
  { value: 'unodc', label: 'UNODC' },
  { value: 'worldbank', label: 'World Bank' },
  { value: 'ilostat', label: 'ILO STAT' },
  { value: 'stateofchildren', label: 'State of Children' },
  { value: 'kpcpwc', label: 'KP CPWC' },
];

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

export function StatisticalReports() {
  const [selectedSource, setSelectedSource] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['statistical-reports', selectedSource],
    queryFn: () =>
      fetchStatisticalReports({
        sourceName: selectedSource || undefined,
      }),
  });

  const chartData = React.useMemo(() => {
    if (!data || data.length === 0) return [];
    const byYear = new Map<number, { year: number; total: number; count: number }>();
    for (const row of data) {
      if (row.reportYear == null || row.value == null) continue;
      const existing = byYear.get(row.reportYear);
      if (existing) {
        existing.total += row.value;
        existing.count += 1;
      } else {
        byYear.set(row.reportYear, { year: row.reportYear, total: row.value, count: 1 });
      }
    }
    return Array.from(byYear.values())
      .map((r) => ({ year: r.year, value: Math.round(r.total) }))
      .sort((a, b) => a.year - b.year);
  }, [data]);

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-[#F59E0B]" />
          <h3 className="text-sm font-semibold text-[#F8FAFC]">Statistical Reports</h3>
        </div>
        <select
          value={selectedSource}
          onChange={(e) => setSelectedSource(e.target.value)}
          className="rounded-md border border-[#334155] bg-[#0F172A] px-2 py-1 text-xs text-[#F8FAFC] outline-none"
        >
          {SOURCE_OPTIONS.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>
      <div className="h-48 sm:h-64">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-[#94A3B8]">No statistical report data available</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="year" stroke="#94A3B8" tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <YAxis stroke="#94A3B8" tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" name="Value" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      {data && data.length > 0 && (
        <p className="text-[10px] text-[#94A3B8] mt-2">
          {data.length} indicator(s) from {new Set(data.map((d) => d.sourceName)).size} source(s)
        </p>
      )}
    </div>
  );
}
