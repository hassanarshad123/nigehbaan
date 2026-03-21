'use client';

import React, { useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { Header } from '@/components/layout/Header';
import { ScraperSummaryCards } from '@/components/scrapers/ScraperSummaryCards';
import { ScraperList } from '@/components/scrapers/ScraperList';
import { ScraperDetail } from '@/components/scrapers/ScraperDetail';
import { ActivityFeed } from '@/components/scrapers/ActivityFeed';
import { useScraperStore } from '@/stores/scraperStore';
import {
  Search,
  PlayCircle,
  Loader2,
  Terminal,
  ArrowLeft,
} from 'lucide-react';
import { triggerAllScrapers, type TriggerResponse } from '@/lib/api';

// ── Filter config ────────────────────────────────────────────────

type StatusFilterValue = 'all' | 'healthy' | 'error' | 'inactive';

interface FilterTab {
  readonly value: StatusFilterValue;
  readonly label: string;
}

const FILTER_TABS: readonly FilterTab[] = [
  { value: 'all', label: 'All' },
  { value: 'healthy', label: 'Healthy' },
  { value: 'error', label: 'Error' },
  { value: 'inactive', label: 'Inactive' },
] as const;

// ── Empty state ──────────────────────────────────────────────────

function EmptyDetailState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#334155]/30 mb-4">
        <Terminal className="h-8 w-8 text-[#64748B]" />
      </div>
      <h3 className="text-sm font-medium text-[#F8FAFC] mb-1">
        Select a scraper
      </h3>
      <p className="text-xs text-[#64748B] max-w-[220px]">
        Choose a scraper from the list to view details, run history, and controls.
      </p>
    </div>
  );
}

// ── Page component ──────────────────────────────────────────────

export default function ScrapersCommandCenter() {
  const queryClient = useQueryClient();
  const {
    selectedScraper,
    setSelectedScraper,
    statusFilter,
    setStatusFilter,
    searchQuery,
    setSearchQuery,
  } = useScraperStore();

  const runAllMutation = useMutation<TriggerResponse[], Error>({
    mutationFn: triggerAllScrapers,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrapers'] });
      queryClient.invalidateQueries({ queryKey: ['scrapers-summary'] });
      queryClient.invalidateQueries({ queryKey: ['scraper-activity'] });
      queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
    },
  });

  const handleFilterChange = useCallback(
    (filter: StatusFilterValue) => {
      setStatusFilter(filter);
    },
    [setStatusFilter],
  );

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value);
    },
    [setSearchQuery],
  );

  const handleBackToList = useCallback(() => {
    setSelectedScraper(null);
  }, [setSelectedScraper]);

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="pt-12">
        {/* Command bar */}
        <div className="border-b border-[#334155] bg-[#0F172A]/95 backdrop-blur-sm sticky top-12 z-40">
          <div className="mx-auto max-w-screen-2xl px-4 py-2.5 flex items-center gap-2 flex-wrap">
            {/* Search input */}
            <div className="relative flex-1 min-w-[180px] max-w-xs">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#64748B]" />
              <input
                type="text"
                placeholder="Search scrapers..."
                value={searchQuery}
                onChange={handleSearchChange}
                className={cn(
                  'w-full rounded-md bg-[#1E293B] border border-[#334155] pl-8 pr-3 py-1.5',
                  'text-xs text-[#F8FAFC] placeholder:text-[#64748B]',
                  'focus:outline-none focus:ring-1 focus:ring-[#06B6D4] focus:border-[#06B6D4]',
                  'transition-colors',
                )}
              />
            </div>

            {/* Filter buttons */}
            <div className="flex items-center gap-0.5 rounded-md bg-[#1E293B] border border-[#334155] p-0.5">
              {FILTER_TABS.map((tab) => (
                <button
                  key={tab.value}
                  type="button"
                  onClick={() => handleFilterChange(tab.value)}
                  className={cn(
                    'rounded px-2.5 py-1 text-[11px] font-medium transition-colors',
                    statusFilter === tab.value
                      ? 'bg-[#334155] text-[#F8FAFC]'
                      : 'text-[#94A3B8] hover:text-[#F8FAFC]',
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Run All button */}
            <button
              type="button"
              disabled={runAllMutation.isPending}
              onClick={() => runAllMutation.mutate()}
              className={cn(
                'ml-auto inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                'bg-[#06B6D4] text-[#0F172A] hover:bg-[#06B6D4]/80',
                'disabled:opacity-50 disabled:cursor-not-allowed',
              )}
            >
              {runAllMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <PlayCircle className="h-3.5 w-3.5" />
              )}
              Run All
            </button>
          </div>

          {/* Run All feedback */}
          {runAllMutation.isSuccess && (
            <div className="mx-auto max-w-screen-2xl px-4 pb-2">
              <div className="rounded-md bg-[#10B981]/10 border border-[#10B981]/20 px-3 py-1.5 text-xs text-[#10B981]">
                Triggered {runAllMutation.data.length} scrapers successfully
              </div>
            </div>
          )}
          {runAllMutation.isError && (
            <div className="mx-auto max-w-screen-2xl px-4 pb-2">
              <div className="rounded-md bg-[#EF4444]/10 border border-[#EF4444]/20 px-3 py-1.5 text-xs text-[#EF4444]">
                Failed to trigger scrapers: {runAllMutation.error.message}
              </div>
            </div>
          )}
        </div>

        {/* Main content — 2-panel layout */}
        <div className="mx-auto max-w-screen-2xl">
          {/* Desktop layout */}
          <div className="hidden md:flex h-[calc(100vh-7rem)]">
            {/* Left panel — fixed width */}
            <div className="w-[380px] flex-shrink-0 border-r border-[#334155] flex flex-col overflow-hidden">
              {/* KPI cards */}
              <div className="p-3 border-b border-[#334155]">
                <ScraperSummaryCards />
              </div>

              {/* Scraper list */}
              <div className="flex-1 overflow-hidden border-b border-[#334155]">
                <div className="px-3 py-2">
                  <h3 className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
                    Scrapers
                  </h3>
                </div>
                <ScraperList />
              </div>

              {/* Activity feed */}
              <div className="flex-shrink-0 overflow-hidden">
                <div className="px-3 py-2 border-b border-[#334155]/50">
                  <h3 className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
                    Live Activity
                  </h3>
                </div>
                <ActivityFeed />
              </div>
            </div>

            {/* Right panel — detail */}
            <div className="flex-1 overflow-hidden">
              {selectedScraper ? (
                <ScraperDetail scraperName={selectedScraper} />
              ) : (
                <EmptyDetailState />
              )}
            </div>
          </div>

          {/* Mobile layout — single column */}
          <div className="md:hidden">
            {selectedScraper ? (
              /* Detail view on mobile */
              <div className="min-h-[calc(100vh-7rem)]">
                <button
                  type="button"
                  onClick={handleBackToList}
                  className="flex items-center gap-1.5 px-4 py-2.5 text-xs text-[#06B6D4] hover:text-[#06B6D4]/80 transition-colors"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Back to list
                </button>
                <ScraperDetail scraperName={selectedScraper} />
              </div>
            ) : (
              /* List view on mobile */
              <div className="space-y-0">
                {/* KPI cards */}
                <div className="p-3 border-b border-[#334155]">
                  <ScraperSummaryCards />
                </div>

                {/* Scraper list */}
                <div className="border-b border-[#334155]">
                  <div className="px-3 py-2">
                    <h3 className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
                      Scrapers
                    </h3>
                  </div>
                  <ScraperList />
                </div>

                {/* Activity feed */}
                <div>
                  <div className="px-3 py-2 border-b border-[#334155]/50">
                    <h3 className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
                      Live Activity
                    </h3>
                  </div>
                  <ActivityFeed />
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
