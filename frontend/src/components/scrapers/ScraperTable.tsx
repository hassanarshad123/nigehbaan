'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { ExternalLink } from 'lucide-react';
import { fetchScrapers, type ScraperStatusResponse } from '@/lib/api';
import { FadeIn } from '@/components/ui/FadeIn';

// ── Status badge ────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { dot: string; bg: string; label: string }> = {
  healthy: { dot: 'bg-[#10B981]', bg: 'bg-[#10B981]/10 text-[#10B981]', label: 'Healthy' },
  warning: { dot: 'bg-[#F59E0B]', bg: 'bg-[#F59E0B]/10 text-[#F59E0B]', label: 'Warning' },
  error:   { dot: 'bg-[#EF4444]', bg: 'bg-[#EF4444]/10 text-[#EF4444]', label: 'Error' },
  inactive:{ dot: 'bg-[#64748B]', bg: 'bg-[#64748B]/10 text-[#64748B]', label: 'Inactive' },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.inactive;
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium', cfg.bg)}>
      <span className={cn('h-1.5 w-1.5 rounded-full', cfg.dot)} />
      {cfg.label}
    </span>
  );
}

// ── Relative time helper ────────────────────────────────────────

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

// ── Source-type labels ──────────────────────────────────────────

const TYPE_LABELS: Record<string, string> = {
  news: 'News',
  court: 'Courts',
  government: 'Government',
  international: 'International',
  report: 'Reports',
};

// ── Table ───────────────────────────────────────────────────────

type SortField = 'status' | 'name' | 'lastScraped';
type SortDir = 'asc' | 'desc';

const STATUS_ORDER: Record<string, number> = { error: 0, warning: 1, healthy: 2, inactive: 3 };

function sortScrapers(
  list: ScraperStatusResponse[],
  field: SortField,
  dir: SortDir,
): ScraperStatusResponse[] {
  const sorted = [...list].sort((a, b) => {
    if (field === 'status') {
      return (STATUS_ORDER[a.status] ?? 4) - (STATUS_ORDER[b.status] ?? 4);
    }
    if (field === 'name') {
      return a.name.localeCompare(b.name);
    }
    // lastScraped — nulls last
    const ta = a.lastScraped ? new Date(a.lastScraped).getTime() : 0;
    const tb = b.lastScraped ? new Date(b.lastScraped).getTime() : 0;
    return ta - tb;
  });
  return dir === 'desc' ? sorted.reverse() : sorted;
}

interface ScraperTableProps {
  statusFilter?: string;
}

export function ScraperTable({ statusFilter = 'all' }: ScraperTableProps) {
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['scrapers'],
    queryFn: fetchScrapers,
    refetchInterval: 30_000,
  });

  const [sortField, setSortField] = React.useState<SortField>('status');
  const [sortDir, setSortDir] = React.useState<SortDir>('asc');

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const data = React.useMemo(() => {
    if (!rawData) return undefined;
    if (statusFilter === 'all') return rawData;
    return rawData.filter((s) => s.status === statusFilter);
  }, [rawData, statusFilter]);

  const grouped = React.useMemo(() => {
    if (!data) return {};
    const sorted = sortScrapers(data, sortField, sortDir);
    const groups: Record<string, ScraperStatusResponse[]> = {};
    for (const s of sorted) {
      const key = s.sourceType ?? 'other';
      if (!groups[key]) groups[key] = [];
      groups[key].push(s);
    }
    return groups;
  }, [data, sortField, sortDir]);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
        {/* Desktop skeleton */}
        <div className="hidden md:block">
          <div className="skeleton h-10 w-full" />
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="flex gap-4 px-4 py-3 border-b border-[#334155]/30">
              <div className="skeleton h-5 w-20 rounded-full" />
              <div className="skeleton h-5 flex-1 rounded" />
              <div className="skeleton h-5 w-24 rounded" />
              <div className="skeleton h-5 w-16 rounded" />
            </div>
          ))}
        </div>
        {/* Mobile skeleton */}
        <div className="md:hidden space-y-2 p-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="skeleton h-24 rounded-md" />
          ))}
        </div>
      </div>
    );
  }

  const sortIndicator = (field: SortField) =>
    sortField === field ? (sortDir === 'asc' ? ' \u2191' : ' \u2193') : '';

  return (
    <FadeIn>
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
      {/* Desktop table */}
      <div className="hidden md:block">
        {/* Table header */}
        <div className="grid grid-cols-[140px_1fr_140px_120px_100px_90px] gap-2 px-4 py-2.5 border-b border-[#334155] text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
          <button type="button" className="text-left hover:text-[#F8FAFC]" onClick={() => handleSort('status')}>
            Status{sortIndicator('status')}
          </button>
          <button type="button" className="text-left hover:text-[#F8FAFC]" onClick={() => handleSort('name')}>
            Name{sortIndicator('name')}
          </button>
          <span>Schedule</span>
          <button type="button" className="text-left hover:text-[#F8FAFC]" onClick={() => handleSort('lastScraped')}>
            Last Run{sortIndicator('lastScraped')}
          </button>
          <span className="text-right">Records</span>
          <span className="text-right">24h</span>
        </div>

        {/* Grouped rows */}
        {Object.entries(grouped).map(([type, scrapers]) => (
          <div key={type}>
            <div className="px-4 py-2 bg-[#0F172A]/50 border-b border-[#334155]">
              <span className="text-xs font-semibold text-[#06B6D4] uppercase tracking-wider">
                {TYPE_LABELS[type] ?? type}
              </span>
            </div>
            {scrapers.map((s) => (
              <div
                key={s.id}
                className="grid grid-cols-[140px_1fr_140px_120px_100px_90px] gap-2 px-4 py-2.5 border-b border-[#334155]/50 hover:bg-[#334155]/20 transition-colors"
              >
                <div>
                  <StatusBadge status={s.status} />
                </div>
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-sm text-[#F8FAFC] truncate">{s.name}</span>
                  {s.url && (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#94A3B8] hover:text-[#06B6D4] flex-shrink-0"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
                <span className="text-xs text-[#94A3B8]">{s.schedule ?? '—'}</span>
                <span className="text-xs text-[#94A3B8]">{relativeTime(s.lastScraped)}</span>
                <span className="text-xs text-[#F8FAFC] text-right tabular-nums">
                  {(s.recordCount ?? 0).toLocaleString()}
                </span>
                <span className="text-xs text-[#F8FAFC] text-right tabular-nums">
                  {s.articlesLast24h}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Mobile card view */}
      <div className="md:hidden space-y-0">
        {Object.entries(grouped).map(([type, scrapers]) => (
          <div key={type}>
            <div className="px-4 py-2 bg-[#0F172A]/50 border-b border-[#334155]">
              <span className="text-xs font-semibold text-[#06B6D4] uppercase tracking-wider">
                {TYPE_LABELS[type] ?? type}
              </span>
            </div>
            {scrapers.map((s) => (
              <div
                key={s.id}
                className="rounded-md bg-[#0F172A] p-3 mx-2 my-2 border-b border-[#334155]/50"
              >
                {/* Top row: status + name + link */}
                <div className="flex items-center gap-2 mb-2">
                  <StatusBadge status={s.status} />
                  <span className="text-sm text-[#F8FAFC] truncate flex-1">{s.name}</span>
                  {s.url && (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#94A3B8] hover:text-[#06B6D4] flex-shrink-0"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                  <div>
                    <span className="text-[#94A3B8]">Schedule: </span>
                    <span className="text-[#F8FAFC]">{s.schedule ?? '—'}</span>
                  </div>
                  <div>
                    <span className="text-[#94A3B8]">Last: </span>
                    <span className="text-[#F8FAFC]">{relativeTime(s.lastScraped)}</span>
                  </div>
                  <div>
                    <span className="text-[#94A3B8]">Records: </span>
                    <span className="text-[#F8FAFC] tabular-nums">{(s.recordCount ?? 0).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-[#94A3B8]">24h: </span>
                    <span className="text-[#F8FAFC] tabular-nums">{s.articlesLast24h}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Empty state */}
      {data && data.length === 0 && (
        <div className="flex items-center justify-center h-32 text-sm text-[#94A3B8]">
          No scrapers found
        </div>
      )}
    </div>
    </FadeIn>
  );
}
