'use client';

import React, { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cn, formatNumber } from '@/lib/utils';
import {
  Play,
  Square,
  ToggleLeft,
  ToggleRight,
  Calendar,
  Clock,
  Database,
  Newspaper,
  ExternalLink,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import {
  fetchScrapers,
  fetchQueueStats,
  triggerScraper,
  stopScraper,
  toggleScraper,
  type ScraperStatusResponse,
  type TriggerResponse,
} from '@/lib/api';
import { RunHistory } from './RunHistory';

// ── Constants ────────────────────────────────────────────────────

const STATUS_BADGE_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  healthy: { bg: 'bg-[#10B981]/15', text: 'text-[#10B981]', label: 'Healthy' },
  warning: { bg: 'bg-[#F59E0B]/15', text: 'text-[#F59E0B]', label: 'Warning' },
  error:   { bg: 'bg-[#EF4444]/15', text: 'text-[#EF4444]', label: 'Error' },
  inactive:{ bg: 'bg-[#64748B]/15', text: 'text-[#64748B]', label: 'Inactive' },
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  news: 'News',
  court: 'Courts',
  government: 'Government',
  international: 'International',
  report: 'Reports',
};

// ── Helpers ──────────────────────────────────────────────────────

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

// ── Info row ─────────────────────────────────────────────────────

interface InfoRowProps {
  readonly icon: React.ReactNode;
  readonly label: string;
  readonly value: React.ReactNode;
}

function InfoRow({ icon, label, value }: InfoRowProps) {
  return (
    <div className="flex items-center gap-2.5 py-2 border-b border-[#334155]/30 last:border-b-0">
      <span className="text-[#64748B] flex-shrink-0">{icon}</span>
      <span className="text-xs text-[#94A3B8] w-24 flex-shrink-0">{label}</span>
      <span className="text-xs text-[#F8FAFC] truncate">{value}</span>
    </div>
  );
}

// ── Skeleton ─────────────────────────────────────────────────────

function DetailSkeleton() {
  return (
    <div className="p-5 space-y-4 animate-pulse">
      <div className="h-7 w-48 rounded bg-[#334155]" />
      <div className="flex gap-2">
        <div className="h-5 w-16 rounded-full bg-[#334155]" />
        <div className="h-5 w-20 rounded-full bg-[#334155]" />
      </div>
      <div className="space-y-3 mt-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex gap-2">
            <div className="h-4 w-4 rounded bg-[#334155]" />
            <div className="h-4 w-20 rounded bg-[#334155]" />
            <div className="h-4 flex-1 rounded bg-[#334155]" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Exported component ──────────────────────────────────────────

interface ScraperDetailProps {
  readonly scraperName: string;
}

export function ScraperDetail({ scraperName }: ScraperDetailProps) {
  const queryClient = useQueryClient();

  const { data: scrapers, isLoading: scrapersLoading } = useQuery({
    queryKey: ['scrapers'],
    queryFn: fetchScrapers,
    refetchInterval: 15_000,
  });

  const { data: queueStats } = useQuery({
    queryKey: ['queue-stats'],
    queryFn: fetchQueueStats,
    refetchInterval: 5_000,
  });

  const scraper: ScraperStatusResponse | undefined = useMemo(() => {
    if (!scrapers) return undefined;
    return scrapers.find(
      (s) => s.scraperName === scraperName || s.name === scraperName,
    );
  }, [scrapers, scraperName]);

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['scrapers'] });
    queryClient.invalidateQueries({ queryKey: ['scrapers-summary'] });
    queryClient.invalidateQueries({ queryKey: ['scraper-activity'] });
    queryClient.invalidateQueries({ queryKey: ['scraper-logs', scraperName] });
    queryClient.invalidateQueries({ queryKey: ['queue-stats'] });
  };

  const triggerMutation = useMutation<TriggerResponse, Error>({
    mutationFn: () => triggerScraper(scraperName),
    onSuccess: invalidateAll,
  });

  const toggleMutation = useMutation<TriggerResponse, Error>({
    mutationFn: () => toggleScraper(scraperName),
    onSuccess: invalidateAll,
  });

  const stopMutation = useMutation<TriggerResponse, Error>({
    mutationFn: () => {
      const activeTask = queueStats?.activeDetails?.find(
        (t) => t.name.includes(scraperName),
      );
      const taskId = activeTask?.id ?? '';
      return stopScraper(scraperName, taskId);
    },
    onSuccess: invalidateAll,
  });

  if (scrapersLoading) {
    return <DetailSkeleton />;
  }

  if (!scraper) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-[#64748B]">
        Scraper not found
      </div>
    );
  }

  const statusBadge = STATUS_BADGE_STYLES[scraper.status] ?? STATUS_BADGE_STYLES.inactive;
  const sourceLabel = SOURCE_TYPE_LABELS[scraper.sourceType ?? ''] ?? scraper.sourceType ?? 'Unknown';
  const isRunning = queueStats?.activeDetails?.some((t) => t.name.includes(scraperName)) ?? false;
  const isMutating = triggerMutation.isPending || toggleMutation.isPending || stopMutation.isPending;

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header section */}
      <div className="p-5 border-b border-[#334155]">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h2 className="text-lg font-bold text-[#F8FAFC] leading-tight">
            {scraper.name}
          </h2>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
              statusBadge.bg,
              statusBadge.text,
            )}
          >
            <span
              className={cn(
                'h-1.5 w-1.5 rounded-full',
                scraper.status === 'healthy' ? 'bg-[#10B981]' :
                scraper.status === 'warning' ? 'bg-[#F59E0B]' :
                scraper.status === 'error' ? 'bg-[#EF4444]' : 'bg-[#64748B]',
              )}
            />
            {statusBadge.label}
          </span>
          <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider bg-[#06B6D4]/10 text-[#06B6D4]">
            {sourceLabel}
          </span>
          {isRunning && (
            <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-[#06B6D4]/15 text-[#06B6D4]">
              <Loader2 className="h-3 w-3 animate-spin" />
              Running
            </span>
          )}
        </div>
      </div>

      {/* Info grid */}
      <div className="px-5 py-3 border-b border-[#334155]">
        <InfoRow
          icon={<Calendar className="h-3.5 w-3.5" />}
          label="Schedule"
          value={scraper.schedule ?? 'Not scheduled'}
        />
        <InfoRow
          icon={<Clock className="h-3.5 w-3.5" />}
          label="Last Run"
          value={relativeTime(scraper.lastScraped)}
        />
        <InfoRow
          icon={<Database className="h-3.5 w-3.5" />}
          label="Records"
          value={formatNumber(scraper.recordCount)}
        />
        <InfoRow
          icon={<Newspaper className="h-3.5 w-3.5" />}
          label="Articles 24h"
          value={formatNumber(scraper.articlesLast24h)}
        />
        {scraper.url && (
          <InfoRow
            icon={<ExternalLink className="h-3.5 w-3.5" />}
            label="URL"
            value={
              <a
                href={scraper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#06B6D4] hover:underline truncate"
              >
                {scraper.url}
              </a>
            }
          />
        )}
      </div>

      {/* Control buttons */}
      <div className="px-5 py-3 flex items-center gap-2 border-b border-[#334155]">
        <button
          type="button"
          disabled={isMutating || isRunning}
          onClick={() => triggerMutation.mutate()}
          className={cn(
            'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            'bg-[#06B6D4] text-[#0F172A] hover:bg-[#06B6D4]/80',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {triggerMutation.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Play className="h-3.5 w-3.5" />
          )}
          Run Now
        </button>

        <button
          type="button"
          disabled={isMutating}
          onClick={() => toggleMutation.mutate()}
          className={cn(
            'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            'bg-[#F59E0B]/15 text-[#F59E0B] hover:bg-[#F59E0B]/25',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {toggleMutation.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : scraper.isActive ? (
            <ToggleRight className="h-3.5 w-3.5" />
          ) : (
            <ToggleLeft className="h-3.5 w-3.5" />
          )}
          {scraper.isActive ? 'Disable' : 'Enable'}
        </button>

        {isRunning && (
          <button
            type="button"
            disabled={isMutating}
            onClick={() => stopMutation.mutate()}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
              'border border-[#EF4444]/50 text-[#EF4444] hover:bg-[#EF4444]/10',
              'disabled:opacity-50 disabled:cursor-not-allowed',
            )}
          >
            {stopMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Square className="h-3.5 w-3.5" />
            )}
            Stop
          </button>
        )}
      </div>

      {/* Mutation feedback messages */}
      {triggerMutation.isSuccess && (
        <div className="mx-5 mt-2 rounded-md bg-[#10B981]/10 border border-[#10B981]/20 px-3 py-2 text-xs text-[#10B981]">
          {triggerMutation.data.message}
        </div>
      )}
      {triggerMutation.isError && (
        <div className="mx-5 mt-2 rounded-md bg-[#EF4444]/10 border border-[#EF4444]/20 px-3 py-2 text-xs text-[#EF4444]">
          Failed to trigger: {triggerMutation.error.message}
        </div>
      )}
      {toggleMutation.isSuccess && (
        <div className="mx-5 mt-2 rounded-md bg-[#F59E0B]/10 border border-[#F59E0B]/20 px-3 py-2 text-xs text-[#F59E0B]">
          {toggleMutation.data.message}
        </div>
      )}
      {stopMutation.isSuccess && (
        <div className="mx-5 mt-2 rounded-md bg-[#F59E0B]/10 border border-[#F59E0B]/20 px-3 py-2 text-xs text-[#F59E0B]">
          {stopMutation.data.message}
        </div>
      )}

      {/* Last error display */}
      {scraper.status === 'error' && scraper.notes && (
        <div className="mx-5 mt-3 rounded-md bg-[#EF4444]/10 border border-[#EF4444]/20 px-3 py-2">
          <div className="flex items-center gap-1.5 mb-1">
            <AlertTriangle className="h-3.5 w-3.5 text-[#EF4444]" />
            <span className="text-xs font-medium text-[#EF4444]">Last Error</span>
          </div>
          <p className="text-xs text-[#EF4444]/80 leading-relaxed">{scraper.notes}</p>
        </div>
      )}

      {/* Run History */}
      <div className="flex-1 px-5 py-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8] mb-2">
          Run History
        </h3>
        <div className="bg-[#0F172A]/50 rounded-lg border border-[#334155]/50 overflow-hidden">
          <RunHistory scraperName={scraperName} />
        </div>
      </div>
    </div>
  );
}
