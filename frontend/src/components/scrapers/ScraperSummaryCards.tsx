'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn, formatNumber } from '@/lib/utils';
import {
  Database,
  Power,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Newspaper,
  Loader2,
} from 'lucide-react';
import { fetchScrapersSummary } from '@/lib/api';

interface SummaryCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

function SummaryCard({ label, value, icon, color, loading }: SummaryCardProps) {
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
          </p>
          <p className="text-xs text-[#94A3B8] mt-1">{label}</p>
        </>
      )}
    </div>
  );
}

export function ScraperSummaryCards() {
  const { data, isLoading } = useQuery({
    queryKey: ['scrapers-summary'],
    queryFn: fetchScrapersSummary,
  });

  const cards: SummaryCardProps[] = [
    {
      label: 'Total Scrapers',
      value: data?.totalScrapers ?? 0,
      icon: <Database className="h-5 w-5" />,
      color: '#06B6D4',
    },
    {
      label: 'Active',
      value: data?.activeScrapers ?? 0,
      icon: <Power className="h-5 w-5" />,
      color: '#8B5CF6',
    },
    {
      label: 'Healthy',
      value: data?.healthyScrapers ?? 0,
      icon: <CheckCircle2 className="h-5 w-5" />,
      color: '#10B981',
    },
    {
      label: 'Warning',
      value: data?.warningScrapers ?? 0,
      icon: <AlertTriangle className="h-5 w-5" />,
      color: '#F59E0B',
    },
    {
      label: 'Error',
      value: data?.errorScrapers ?? 0,
      icon: <XCircle className="h-5 w-5" />,
      color: '#EF4444',
    },
    {
      label: 'Articles (24h)',
      value: data?.articlesLast24h ?? 0,
      icon: <Newspaper className="h-5 w-5" />,
      color: '#06B6D4',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map((card) => (
        <SummaryCard key={card.label} {...card} loading={isLoading} />
      ))}
    </div>
  );
}
