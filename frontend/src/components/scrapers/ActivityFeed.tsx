'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import { fetchScraperActivity, type ScraperRunResponse } from '@/lib/api';
import { useScraperStore } from '@/stores/scraperStore';

// ── Relative time helper ─────────────────────────────────────────

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

// ── Status icon mapping ──────────────────────────────────────────

function StatusIcon({ status }: { readonly status: ScraperRunResponse['status'] }) {
  switch (status) {
    case 'success':
      return <CheckCircle2 className="h-3.5 w-3.5 text-[#10B981] flex-shrink-0" />;
    case 'error':
      return <XCircle className="h-3.5 w-3.5 text-[#EF4444] flex-shrink-0" />;
    case 'running':
      return <Loader2 className="h-3.5 w-3.5 text-[#06B6D4] animate-spin flex-shrink-0" />;
    case 'pending':
      return <Clock className="h-3.5 w-3.5 text-[#F59E0B] flex-shrink-0" />;
    default:
      return <Clock className="h-3.5 w-3.5 text-[#64748B] flex-shrink-0" />;
  }
}

const STATUS_TEXT_COLORS: Record<string, string> = {
  success: 'text-[#10B981]',
  error: 'text-[#EF4444]',
  running: 'text-[#06B6D4]',
  pending: 'text-[#F59E0B]',
};

// ── Format duration ──────────────────────────────────────────────

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '—';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

// ── Skeleton ─────────────────────────────────────────────────────

function FeedSkeleton() {
  return (
    <div className="space-y-2 p-2 animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center gap-2 px-2 py-1.5">
          <div className="h-3.5 w-3.5 rounded-full bg-[#334155]" />
          <div className="h-3 flex-1 rounded bg-[#334155]" />
          <div className="h-3 w-8 rounded bg-[#334155]" />
        </div>
      ))}
    </div>
  );
}

// ── Feed entry ──────────────────────────────────────────────────

interface FeedEntryProps {
  readonly run: ScraperRunResponse;
  readonly onClickScraper: (name: string) => void;
}

function FeedEntry({ run, onClickScraper }: FeedEntryProps) {
  const textColor = STATUS_TEXT_COLORS[run.status] ?? 'text-[#94A3B8]';
  const timeStr = relativeTime(run.startedAt ?? run.completedAt);

  return (
    <div className="flex items-start gap-2 px-2 py-1.5 rounded hover:bg-[#334155]/20 transition-colors">
      <StatusIcon status={run.status} />
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-1.5">
          <button
            type="button"
            onClick={() => onClickScraper(run.scraperName)}
            className={cn('text-xs font-medium truncate hover:underline', textColor)}
          >
            {run.scraperName}
          </button>
          <span className="text-xs text-[#64748B] flex-shrink-0">{timeStr}</span>
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          {run.recordsSaved > 0 && (
            <span className="text-xs text-[#94A3B8] tabular-nums">
              {run.recordsSaved} saved
            </span>
          )}
          {run.durationSeconds !== null && run.durationSeconds !== undefined && (
            <span className="text-xs text-[#64748B] tabular-nums">
              {formatDuration(run.durationSeconds)}
            </span>
          )}
          {run.status === 'error' && run.errorMessage && (
            <span className="text-xs text-[#EF4444] truncate max-w-[120px]">
              {run.errorMessage}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Exported component ──────────────────────────────────────────

export function ActivityFeed() {
  const { setSelectedScraper } = useScraperStore();

  const { data: activity, isLoading } = useQuery({
    queryKey: ['scraper-activity'],
    queryFn: () => fetchScraperActivity(30),
    refetchInterval: 5_000,
  });

  if (isLoading) {
    return <FeedSkeleton />;
  }

  if (!activity || activity.length === 0) {
    return (
      <div className="flex items-center justify-center py-6 text-xs text-[#64748B]">
        No recent activity
      </div>
    );
  }

  return (
    <div className="overflow-y-auto max-h-48 space-y-0.5">
      {activity.map((run) => (
        <FeedEntry
          key={run.id}
          run={run}
          onClickScraper={setSelectedScraper}
        />
      ))}
    </div>
  );
}
