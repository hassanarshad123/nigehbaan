'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Eye } from 'lucide-react';
import { fetchTransparencyReports } from '@/lib/api';
import type { TransparencyReportItem } from '@/lib/api';

export function TransparencyMetrics() {
  const { data, isLoading } = useQuery({
    queryKey: ['transparency-reports'],
    queryFn: () => fetchTransparencyReports(),
  });

  const grouped = React.useMemo(() => {
    if (!data || data.length === 0) return new Map<string, TransparencyReportItem[]>();
    const map = new Map<string, TransparencyReportItem[]>();
    for (const item of data) {
      const key = item.platform;
      const list = map.get(key) ?? [];
      list.push(item);
      map.set(key, list);
    }
    return map;
  }, [data]);

  const platforms = Array.from(grouped.keys());

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <div className="flex items-center gap-2 mb-4">
        <Eye className="h-4 w-4 text-[#06B6D4]" />
        <h3 className="text-sm font-semibold text-[#F8FAFC]">Tech Platform Transparency</h3>
      </div>

      {isLoading ? (
        <div className="flex h-32 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
        </div>
      ) : platforms.length === 0 ? (
        <div className="flex h-32 items-center justify-center">
          <p className="text-sm text-[#94A3B8]">No transparency data available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {platforms.map((platform) => {
            const items = grouped.get(platform) ?? [];
            return (
              <div
                key={platform}
                className="rounded-md border border-[#334155] bg-[#0F172A] p-3"
              >
                <p className="text-xs font-semibold text-[#F8FAFC] mb-2 uppercase tracking-wider">
                  {platform}
                </p>
                <div className="space-y-1.5">
                  {items.slice(0, 5).map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs">
                      <span className="text-[#94A3B8] truncate mr-2">
                        {item.metric ?? 'N/A'}
                      </span>
                      <span className="text-[#F8FAFC] font-mono shrink-0">
                        {item.value != null ? item.value.toLocaleString() : '—'}
                        {item.unit ? ` ${item.unit}` : ''}
                      </span>
                    </div>
                  ))}
                  {items.length > 5 && (
                    <p className="text-[10px] text-[#94A3B8]">+{items.length - 5} more metrics</p>
                  )}
                </div>
                {items[0]?.reportPeriod && (
                  <p className="text-[10px] text-[#94A3B8] mt-2">Period: {items[0].reportPeriod}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
