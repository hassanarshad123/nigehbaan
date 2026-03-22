'use client';

import React, { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Footer } from '@/components/layout/Footer';
import { LoginForm } from '@/components/admin/LoginForm';
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
  Eye,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import {
  fetchDashboardSummary,
  fetchScrapersSummary,
  fetchPendingReports,
  fetchScrapers,
  updateReportStatus,
} from '@/lib/api';

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

function AdminDashboard() {
  const queryClient = useQueryClient();
  const [actionLoading, setActionLoading] = useState<number | null>(null);

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
    queryFn: () => fetchPendingReports({ limit: 20 }),
  });

  const { data: scrapers } = useQuery({
    queryKey: ['admin-scrapers'],
    queryFn: fetchScrapers,
  });

  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateReportStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-reports'] });
      setActionLoading(null);
    },
    onError: () => {
      setActionLoading(null);
    },
  });

  const handleStatusChange = (reportId: number, newStatus: string) => {
    setActionLoading(reportId);
    mutation.mutate({ id: reportId, status: newStatus });
  };

  const topScrapers = (scrapers ?? [])
    .sort((a, b) => (b.recordCount ?? 0) - (a.recordCount ?? 0))
    .slice(0, 6);

  return (
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
                  className="rounded-md bg-[#0F172A] px-3 py-2.5"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-[#06B6D4]">#{report.id}</span>
                      <span className="text-xs text-[#F8FAFC] capitalize">
                        {report.reportType.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-[#94A3B8] tabular-nums">
                        {new Date(report.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
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
                  {/* Action buttons */}
                  {report.status === 'pending' && (
                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => handleStatusChange(report.id, 'under_review')}
                        disabled={actionLoading === report.id}
                        className="flex items-center gap-1 rounded px-2 py-1 text-[10px] font-medium text-[#F59E0B] bg-[#F59E0B]/10 hover:bg-[#F59E0B]/20 transition-default"
                        aria-label={`Review report ${report.id}`}
                      >
                        <Eye className="h-3 w-3" />
                        Review
                      </button>
                      <button
                        onClick={() => handleStatusChange(report.id, 'verified')}
                        disabled={actionLoading === report.id}
                        className="flex items-center gap-1 rounded px-2 py-1 text-[10px] font-medium text-[#10B981] bg-[#10B981]/10 hover:bg-[#10B981]/20 transition-default"
                        aria-label={`Verify report ${report.id}`}
                      >
                        <ThumbsUp className="h-3 w-3" />
                        Verify
                      </button>
                      <button
                        onClick={() => handleStatusChange(report.id, 'rejected')}
                        disabled={actionLoading === report.id}
                        className="flex items-center gap-1 rounded px-2 py-1 text-[10px] font-medium text-[#EF4444] bg-[#EF4444]/10 hover:bg-[#EF4444]/20 transition-default"
                        aria-label={`Reject report ${report.id}`}
                      >
                        <ThumbsDown className="h-3 w-3" />
                        Reject
                      </button>
                      {actionLoading === report.id && (
                        <Loader2 className="h-3 w-3 animate-spin text-[#94A3B8]" />
                      )}
                    </div>
                  )}
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
  );
}

export default function AdminPage() {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#06B6D4]" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <LoginForm />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <AdminDashboard />
      <Footer />
    </div>
  );
}
