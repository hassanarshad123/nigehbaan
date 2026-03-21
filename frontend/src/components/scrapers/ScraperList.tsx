'use client';

import React, { useMemo, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { fetchScrapers, type ScraperStatusResponse } from '@/lib/api';
import { useScraperStore } from '@/stores/scraperStore';

// ── Constants ────────────────────────────────────────────────────

const STATUS_DOT_COLORS: Record<string, string> = {
  healthy: 'bg-[#10B981]',
  warning: 'bg-[#F59E0B]',
  error: 'bg-[#EF4444]',
  inactive: 'bg-[#64748B]',
};

const GROUP_LABELS: Record<string, string> = {
  news: 'News',
  court: 'Courts',
  government: 'Government',
  international: 'International',
  report: 'Reports',
};

const GROUP_ORDER = ['news', 'court', 'government', 'international', 'report'];

// ── Relative time helper ─────────────────────────────────────────

function relativeTime(iso: string | null): string {
  if (!iso) return 'Never';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

// ── Skeleton ─────────────────────────────────────────────────────

function ListSkeleton() {
  return (
    <div className="space-y-1 animate-pulse">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="flex items-center gap-2 px-3 py-2">
          <div className="h-2 w-2 rounded-full bg-[#334155]" />
          <div className="h-4 flex-1 rounded bg-[#334155]" />
          <div className="h-3 w-10 rounded bg-[#334155]" />
        </div>
      ))}
    </div>
  );
}

// ── Group section ────────────────────────────────────────────────

interface GroupSectionProps {
  readonly groupKey: string;
  readonly scrapers: readonly ScraperStatusResponse[];
  readonly selectedScraper: string | null;
  readonly onSelect: (name: string) => void;
}

function GroupSection({ groupKey, scrapers, selectedScraper, onSelect }: GroupSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const toggleExpanded = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <div>
      <button
        type="button"
        onClick={toggleExpanded}
        className="flex w-full items-center gap-1.5 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8] hover:text-[#F8FAFC] transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        <span>{GROUP_LABELS[groupKey] ?? groupKey}</span>
        <span className="ml-auto text-[10px] font-normal text-[#64748B] tabular-nums">
          {scrapers.length}
        </span>
      </button>

      {isExpanded && (
        <div>
          {scrapers.map((s) => {
            const isSelected = selectedScraper === s.scraperName;
            const dotColor = STATUS_DOT_COLORS[s.status] ?? STATUS_DOT_COLORS.inactive;

            return (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelect(s.scraperName ?? s.name)}
                className={cn(
                  'flex w-full items-center gap-2 px-3 py-1.5 text-left transition-colors',
                  'hover:bg-[#334155]/30',
                  isSelected
                    ? 'bg-[#334155]/40 border-l-2 border-[#06B6D4]'
                    : 'border-l-2 border-transparent',
                )}
              >
                <span className={cn('h-2 w-2 rounded-full flex-shrink-0', dotColor)} />
                <span
                  className={cn(
                    'text-xs truncate flex-1',
                    isSelected ? 'text-[#F8FAFC] font-medium' : 'text-[#94A3B8]',
                  )}
                >
                  {s.name}
                </span>
                <span className="text-[10px] text-[#64748B] tabular-nums flex-shrink-0">
                  {relativeTime(s.lastScraped)}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Exported component ──────────────────────────────────────────

export function ScraperList() {
  const { selectedScraper, setSelectedScraper, statusFilter, searchQuery } = useScraperStore();

  const { data: scrapers, isLoading } = useQuery({
    queryKey: ['scrapers'],
    queryFn: fetchScrapers,
    refetchInterval: 15_000,
  });

  const filteredScrapers = useMemo(() => {
    if (!scrapers) return [];
    return scrapers.filter((s) => {
      if (statusFilter !== 'all' && s.status !== statusFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const nameMatch = s.name.toLowerCase().includes(q);
        const typeMatch = (s.sourceType ?? '').toLowerCase().includes(q);
        if (!nameMatch && !typeMatch) return false;
      }
      return true;
    });
  }, [scrapers, statusFilter, searchQuery]);

  const grouped = useMemo(() => {
    const groups: Record<string, ScraperStatusResponse[]> = {};
    for (const s of filteredScrapers) {
      const key = s.sourceType ?? 'other';
      if (!groups[key]) groups[key] = [];
      groups[key].push(s);
    }

    const sortedEntries = Object.entries(groups).sort(([a], [b]) => {
      const aIdx = GROUP_ORDER.indexOf(a);
      const bIdx = GROUP_ORDER.indexOf(b);
      const aOrder = aIdx >= 0 ? aIdx : GROUP_ORDER.length;
      const bOrder = bIdx >= 0 ? bIdx : GROUP_ORDER.length;
      return aOrder - bOrder;
    });

    return sortedEntries;
  }, [filteredScrapers]);

  if (isLoading) {
    return <ListSkeleton />;
  }

  if (filteredScrapers.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-xs text-[#64748B]">
        No scrapers match filters
      </div>
    );
  }

  return (
    <div className="space-y-0.5 overflow-y-auto max-h-[calc(100vh-26rem)]">
      {grouped.map(([groupKey, groupScrapers]) => (
        <GroupSection
          key={groupKey}
          groupKey={groupKey}
          scrapers={groupScrapers}
          selectedScraper={selectedScraper}
          onSelect={setSelectedScraper}
        />
      ))}
    </div>
  );
}
