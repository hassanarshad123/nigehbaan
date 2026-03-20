'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn, formatNumber } from '@/lib/utils';
import { AlertTriangle, MapPin, Database, Scale, Loader2 } from 'lucide-react';
import { fetchDashboardSummary } from '@/lib/api';

interface SummaryCardProps {
  label: string;
  value: number;
  suffix?: string;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

function SummaryCard({ label, value, suffix, icon, color, loading }: SummaryCardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border border-[#334155] bg-[#1E293B] p-4 glow-border transition-default',
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${color}15`, color }}
        >
          {icon}
        </div>
      </div>
      {loading ? (
        <div className="flex items-center gap-2 mt-1">
          <Loader2 className="h-4 w-4 animate-spin text-[#94A3B8]" />
          <span className="text-xs text-[#94A3B8]">Loading...</span>
        </div>
      ) : (
        <>
          <p className="text-2xl font-bold text-[#F8FAFC] tabular-nums">
            {formatNumber(value)}
            {suffix && <span className="text-sm font-normal text-[#94A3B8] ml-0.5">{suffix}</span>}
          </p>
          <p className="text-xs text-[#94A3B8] mt-1">{label}</p>
        </>
      )}
    </div>
  );
}

export function SummaryCards() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
  });

  const cards: SummaryCardProps[] = [
    {
      label: 'Total Incidents',
      value: data?.totalIncidents ?? 0,
      icon: <AlertTriangle className="h-5 w-5" />,
      color: '#EF4444',
    },
    {
      label: 'Districts With Data',
      value: data?.districtsWithData ?? 0,
      icon: <MapPin className="h-5 w-5" />,
      color: '#06B6D4',
    },
    {
      label: 'Data Sources',
      value: data?.dataSourcesActive ?? 0,
      icon: <Database className="h-5 w-5" />,
      color: '#10B981',
    },
    {
      label: 'Avg. Conviction Rate',
      value: data?.avgConvictionRate ?? 0,
      suffix: '%',
      icon: <Scale className="h-5 w-5" />,
      color: '#F59E0B',
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <SummaryCard key={card.label} {...card} loading={isLoading} />
      ))}
    </div>
  );
}
