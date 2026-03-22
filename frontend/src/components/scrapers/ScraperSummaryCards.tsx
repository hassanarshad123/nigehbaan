'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { formatNumber } from '@/lib/utils';
import {
  Database,
  CheckCircle2,
  AlertTriangle,
  Newspaper,
} from 'lucide-react';
import { fetchScrapersSummary } from '@/lib/api';

// ── Types ────────────────────────────────────────────────────────

interface MiniCardProps {
  readonly label: string;
  readonly value: number;
  readonly icon: React.ReactNode;
  readonly color: string;
  readonly loading: boolean;
}

// ── Skeleton placeholder ─────────────────────────────────────────

function MiniCardSkeleton() {
  return (
    <div className="bg-[#1E293B]/80 backdrop-blur-sm border border-[#334155] rounded-lg p-3 animate-pulse">
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-md bg-[#334155]" />
        <div className="flex-1 space-y-1.5">
          <div className="h-5 w-10 rounded bg-[#334155]" />
          <div className="h-3 w-16 rounded bg-[#334155]" />
        </div>
      </div>
    </div>
  );
}

// ── Mini KPI card ───────────────────────────────────────────────

function MiniCard({ label, value, icon, color, loading }: MiniCardProps) {
  if (loading) {
    return <MiniCardSkeleton />;
  }

  return (
    <div className="bg-[#1E293B]/80 backdrop-blur-sm border border-[#334155] rounded-lg p-3">
      <div className="flex items-center gap-2">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-md flex-shrink-0"
          style={{ backgroundColor: `${color}15`, color }}
        >
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-lg font-bold text-[#F8FAFC] tabular-nums leading-tight">
            {formatNumber(value)}
          </p>
          <p className="text-xs text-[#94A3B8] uppercase tracking-wider truncate">
            {label}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Exported component ──────────────────────────────────────────

export function ScraperSummaryCards() {
  const { data, isLoading } = useQuery({
    queryKey: ['scrapers-summary'],
    queryFn: fetchScrapersSummary,
    refetchInterval: 15_000,
  });

  const cards: Omit<MiniCardProps, 'loading'>[] = [
    {
      label: 'Total Scrapers',
      value: data?.totalScrapers ?? 0,
      icon: <Database className="h-4 w-4" />,
      color: '#06B6D4',
    },
    {
      label: 'Healthy',
      value: data?.healthyScrapers ?? 0,
      icon: <CheckCircle2 className="h-4 w-4" />,
      color: '#10B981',
    },
    {
      label: 'Errors',
      value: data?.errorScrapers ?? 0,
      icon: <AlertTriangle className="h-4 w-4" />,
      color: '#EF4444',
    },
    {
      label: 'Articles 24h',
      value: data?.articlesLast24h ?? 0,
      icon: <Newspaper className="h-4 w-4" />,
      color: '#06B6D4',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {cards.map((card) => (
        <MiniCard key={card.label} {...card} loading={isLoading} />
      ))}
    </div>
  );
}
