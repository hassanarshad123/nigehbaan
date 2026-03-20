'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { ScraperSummaryCards } from '@/components/scrapers/ScraperSummaryCards';
import { ScraperTable } from '@/components/scrapers/ScraperTable';
import { cn } from '@/lib/utils';
import { fetchScrapersSummary } from '@/lib/api';

type StatusFilter = 'all' | 'healthy' | 'warning' | 'error';

const TABS: { value: StatusFilter; label: string; color: string }[] = [
  { value: 'all', label: 'All', color: 'text-[#F8FAFC]' },
  { value: 'healthy', label: 'Healthy', color: 'text-[#10B981]' },
  { value: 'warning', label: 'Warning', color: 'text-[#F59E0B]' },
  { value: 'error', label: 'Error', color: 'text-[#EF4444]' },
];

export default function ScrapersPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const { data: summary } = useQuery({
    queryKey: ['scrapers-summary'],
    queryFn: fetchScrapersSummary,
  });

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-2xl px-4 pt-16 pb-8">
        {/* Page title */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#F8FAFC]">
              Scrapers Health
            </h1>
            <p className="text-sm text-[#94A3B8] mt-1">
              Real-time monitoring of all data collection scrapers
              {summary?.lastActivity && (
                <span className="ml-2 text-[#64748B]">
                  · Last activity: {new Date(summary.lastActivity).toLocaleString()}
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Summary KPI cards */}
        <div className="mb-6">
          <ScraperSummaryCards />
        </div>

        {/* Status filter tabs */}
        <div className="flex items-center gap-1 mb-4">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={cn(
                'rounded-md px-3 py-1.5 text-xs font-medium transition-default',
                statusFilter === tab.value
                  ? `bg-[#334155] ${tab.color}`
                  : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#334155]/50',
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Scraper status table */}
        <ScraperTable statusFilter={statusFilter} />
      </main>

      <Footer />
    </div>
  );
}
