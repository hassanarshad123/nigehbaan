'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { fetchScraperLogs, type ScraperRunResponse } from '@/lib/api';

// ── Constants ────────────────────────────────────────────────────

const STATUS_DOT_COLORS: Record<string, string> = {
  success: 'bg-[#10B981]',
  error: 'bg-[#EF4444]',
  running: 'bg-[#06B6D4]',
  pending: 'bg-[#F59E0B]',
};

// ── Helpers ──────────────────────────────────────────────────────

function relativeTime(iso: string | null): string {
  if (!iso) return '—';
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

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '—';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

// ── Skeleton ─────────────────────────────────────────────────────

function TableSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-[#334155]/30 rounded mb-1" />
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-3 px-3 py-2">
          <div className="h-2 w-2 rounded-full bg-[#334155] mt-1" />
          <div className="h-4 w-16 rounded bg-[#334155]" />
          <div className="h-4 w-12 rounded bg-[#334155]" />
          <div className="h-4 w-8 rounded bg-[#334155]" />
          <div className="h-4 w-8 rounded bg-[#334155]" />
          <div className="h-4 flex-1 rounded bg-[#334155]" />
        </div>
      ))}
    </div>
  );
}

// ── Row component ───────────────────────────────────────────────

function RunRow({ run }: { readonly run: ScraperRunResponse }) {
  const dotColor = STATUS_DOT_COLORS[run.status] ?? 'bg-[#64748B]';
  const hasError = run.status === 'error' && run.errorMessage;

  return (
    <tr className="border-b border-[#334155]/30 hover:bg-[#334155]/10 transition-colors">
      <td className="px-3 py-1.5">
        <span className={cn('inline-block h-2 w-2 rounded-full', dotColor)} />
      </td>
      <td className="px-3 py-1.5 text-xs text-[#94A3B8] tabular-nums whitespace-nowrap">
        {relativeTime(run.startedAt ?? run.completedAt)}
      </td>
      <td className="px-3 py-1.5 text-xs text-[#94A3B8] tabular-nums whitespace-nowrap">
        {formatDuration(run.durationSeconds)}
      </td>
      <td className="px-3 py-1.5 text-xs text-[#F8FAFC] tabular-nums text-right">
        {run.recordsFound}
      </td>
      <td className="px-3 py-1.5 text-xs text-[#F8FAFC] tabular-nums text-right">
        {run.recordsSaved}
      </td>
      <td className="px-3 py-1.5 text-xs text-[#EF4444] max-w-[180px] truncate" title={run.errorMessage ?? undefined}>
        {hasError ? run.errorMessage : '—'}
      </td>
    </tr>
  );
}

// ── Exported component ──────────────────────────────────────────

interface RunHistoryProps {
  readonly scraperName: string;
}

export function RunHistory({ scraperName }: RunHistoryProps) {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['scraper-logs', scraperName],
    queryFn: () => fetchScraperLogs(scraperName, 15),
    refetchInterval: 10_000,
    enabled: Boolean(scraperName),
  });

  if (isLoading) {
    return <TableSkeleton />;
  }

  if (!runs || runs.length === 0) {
    return (
      <div className="flex items-center justify-center py-6 text-xs text-[#64748B]">
        No run history available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[#334155]">
            <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-[#64748B] w-8" />
            <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]">
              Time
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]">
              Duration
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium uppercase tracking-wider text-[#64748B]">
              Found
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium uppercase tracking-wider text-[#64748B]">
              Saved
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]">
              Error
            </th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <RunRow key={run.id} run={run} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
