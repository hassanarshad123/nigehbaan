'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Footer } from '@/components/layout/Footer';
import { cn, formatNumber } from '@/lib/utils';
import {
  ShieldCheck,
  FileWarning,
  Database,
  Activity,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import {
  fetchDashboardSummary,
  fetchScrapersSummary,
  fetchPendingReports,
  type PendingReportItem,
  type ScraperStatusResponse,
} from '@/lib/api';
import { fetchScrapers } from '@/lib/api';

const STATUS_ICON: Record<string, React.ReactNode> = {
  healthy: <CheckCircle2 className="h-4 w-4 text-[#10B981]" />,
  warning: <AlertTriangle className="h-4 w-4 text-[#F59E0B]" />,
  degraded: <AlertTriangle className="h-4 w-4 text-[#F59E0B]" />,
  error: <XCircle className="h-4 w-4 text-[#EF4444]" />,
  inactive: <Clock className="h-4 w-4 text-[#94A3B8]" />,
};

const REPORT_STATUS_STYLES: Record<string, string> = {
  pending: 'bg-[#06B6D4]/10 text-[#06B6D4]',
  submitted: 'bg-[#06B6D4]/10 text-[#06B6D4]',
  under_review: 'bg-[#F59E0B]/10 text-[#F59E0B]',
  verified: 'bg-[#10B981]/10 text-[#10B981]',
  rejected: 'bg-[#EF4444]/10 text-[#EF4444]',
};

export default function AdminPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['admin-summary'],
    queryFn: fetchDashboardSummary,
  });

  const { data: scrapersSummary } = useQuery({
    queryKey: ['admin-scrapers-summary'],
    queryFn: fetchScrapersSummary,
  });

  const { data: reports, isLoading: reportsLoading } = useQuery({
    queryKey: ['admin-reports'],
    queryFn: () => fetchPendingReports({ limit: 10 }),
  });

  const { data: scrapers } = useQuery({
    queryKey: ['admin-scrapers'],
    queryFn: fetchScrapers,
  });

  // Top 6 scrapers by record count for display
  const topScrapers = (scrapers ?? [])
    .sort((a, b) => (b.recordCount ?? 0) - (a.recordCount ?? 0))
    .slice(0, 6);

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <main className="mx-auto max-w-screen-xl px-4 pt-6 pb-8">
        {/* Header */}
        <div className="flex items-center gap-2 mb-6">
          <ShieldCheck className="h-5 w-5 text-[#06B6D4]" />
          <h1 className="text-2xl font-bold text-[#F8FAFC]">Admin Dashboard</h1>
        </div>

        {/* System stats */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#F59E0B]">
              <FileWarning className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">Pending Reports</span>
            </div>
            <p className="text-2xl font-bold text-[#F8FAFC]">
              {reportsLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : (reports?.length ?? 0)}
            </p>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#10B981]">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">Active Scrapers</span>
            </div>
            <p className="text-2xl font-bold text-[#F8FAFC]">
              {scrapersSummary?.activeScrapers ?? '-'}
            </p>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#06B6D4]">
              <Database className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">Total Incidents</span>
            </div>
            <p className="text-2xl font-bold text-[#F8FAFC]">
              {summaryLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : formatNumber(summary?.totalIncidents ?? 0)}
            </p>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#EC4899]">
              <Activity className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">Healthy Scrapers</span>
            </div>
            <p className="text-2xl font-bold text-[#10B981]">
              {scrapersSummary ? `${scrapersSummary.healthyScrapers}/${scrapersSummary.totalScrapers}` : '-'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Report moderation */}
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <h2 className="text-sm font-semibold text-[#F8FAFC] mb-4 flex items-center gap-2">
              <FileWarning className="h-4 w-4 text-[#F59E0B]" />
              Report Moderation Queue
            </h2>
            {reportsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
              </div>
            ) : (reports ?? []).length === 0 ? (
              <p className="text-sm text-[#94A3B8] text-center py-8">No pending reports</p>
            ) : (
              <div className="space-y-2">
                {(reports ?? []).map((report) => (
                  <div
                    key={report.id}
                    className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between rounded-md bg-[#0F172A] px-3 py-2.5"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-[#06B6D4]">#{report.id}</span>
                      <span className="text-xs text-[#F8FAFC] capitalize">
                        {report.reportType.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#94A3B8] tabular-nums">
                        {new Date(report.createdAt).toLocaleDateString()}
                      </span>
                      <span
                        className={cn(
                          'rounded-full px-2 py-0.5 text-xs font-medium capitalize',
                          REPORT_STATUS_STYLES[report.status] ?? 'text-[#94A3B8]',
                        )}
                      >
                        {report.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Data source health */}
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <h2 className="text-sm font-semibold text-[#F8FAFC] mb-4 flex items-center gap-2">
              <Database className="h-4 w-4 text-[#06B6D4]" />
              Data Source Health
            </h2>
            <div className="space-y-2">
              {topScrapers.map((source) => (
                <div
                  key={source.id}
                  className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between rounded-md bg-[#0F172A] px-3 py-2.5"
                >
                  <div className="flex items-center gap-2">
                    {STATUS_ICON[source.status] ?? STATUS_ICON.inactive}
                    <span className="text-xs text-[#F8FAFC]">{source.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-[#94A3B8] tabular-nums">
                      {formatNumber(source.recordCount)} records
                    </span>
                    {source.lastScraped && (
                      <span className="flex items-center gap-1 text-xs text-[#94A3B8]">
                        <Clock className="h-3 w-3" />
                        {new Date(source.lastScraped).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
