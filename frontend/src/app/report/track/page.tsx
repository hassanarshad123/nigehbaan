'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { cn } from '@/lib/utils';
import { Search, FileCheck, Clock, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { fetchReportStatus } from '@/lib/api';
import { FadeIn } from '@/components/ui/FadeIn';

const STATUS_STYLES: Record<string, { bg: string; label: string }> = {
  submitted: { bg: 'bg-[#06B6D4]/10 text-[#06B6D4]', label: 'Submitted' },
  under_review: { bg: 'bg-[#F59E0B]/10 text-[#F59E0B]', label: 'Under Review' },
  verified: { bg: 'bg-[#10B981]/10 text-[#10B981]', label: 'Verified' },
  rejected: { bg: 'bg-[#EF4444]/10 text-[#EF4444]', label: 'Rejected' },
  pending: { bg: 'bg-[#06B6D4]/10 text-[#06B6D4]', label: 'Pending' },
};

export default function ReportTrackPage() {
  const [refInput, setRefInput] = useState('');
  const [searchId, setSearchId] = useState('');

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['report-status', searchId],
    queryFn: () => fetchReportStatus(searchId),
    enabled: searchId.length > 0,
    retry: false,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = refInput.trim();
    if (cleaned) setSearchId(cleaned);
  };

  const statusInfo = report ? STATUS_STYLES[report.status] ?? STATUS_STYLES.pending : null;

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-lg px-4 pt-24 pb-8">
        <div className="mb-6">
          <Link
            href="/report"
            className="inline-flex items-center gap-1.5 text-sm text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Report
          </Link>
        </div>

        <div className="text-center mb-8">
          <FileCheck className="mx-auto h-10 w-10 text-[#06B6D4] mb-3" />
          <h1 className="text-2xl font-bold text-[#F8FAFC] mb-1">Track Your Report</h1>
          <p className="text-sm text-[#94A3B8]">
            Enter your reference number to check the status of your report.
          </p>
        </div>

        {/* Search form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex gap-2">
            <input
              type="text"
              value={refInput}
              onChange={(e) => setRefInput(e.target.value)}
              placeholder="e.g. NGH-M1234XYZ or report ID"
              className={cn(
                'flex-1 rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2.5 text-sm text-[#F8FAFC]',
                'placeholder-[#94A3B8] outline-none border-glow-focus transition-default',
              )}
            />
            <button
              type="submit"
              disabled={!refInput.trim()}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-4 py-2.5 text-sm font-medium transition-default',
                refInput.trim()
                  ? 'bg-[#06B6D4] text-[#0F172A] hover:bg-[#06B6D4]/90'
                  : 'bg-[#334155] text-[#94A3B8] cursor-not-allowed',
              )}
            >
              <Search className="h-4 w-4" />
              Track
            </button>
          </div>
        </form>

        {/* Loading */}
        {isLoading && (
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6">
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="skeleton h-3 w-20" />
                  <div className="skeleton h-5 w-32 rounded" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && !isLoading && (
          <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 px-4 py-6 text-center">
            <p className="text-sm text-[#EF4444]">
              Report not found. Please check your reference number and try again.
            </p>
          </div>
        )}

        {/* Result */}
        {report && !isLoading && (
          <FadeIn>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-[#94A3B8]">Reference</p>
              <span className="text-sm font-mono font-bold text-[#06B6D4]">
                {report.referenceNumber}
              </span>
            </div>

            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-[#94A3B8]">Status</p>
              {statusInfo && (
                <span className={cn('rounded-full px-3 py-1 text-xs font-medium', statusInfo.bg)}>
                  {statusInfo.label}
                </span>
              )}
            </div>

            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-[#94A3B8]">Report Type</p>
              <span className="text-sm text-[#F8FAFC] capitalize">
                {report.reportType.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-[#94A3B8]">Submitted</p>
              <span className="text-xs text-[#94A3B8] flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {new Date(report.createdAt).toLocaleDateString()}
              </span>
            </div>

            {report.updatedAt && report.updatedAt !== report.createdAt && (
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs text-[#94A3B8]">Last Updated</p>
                <span className="text-xs text-[#94A3B8]">
                  {new Date(report.updatedAt).toLocaleDateString()}
                </span>
              </div>
            )}

            {report.referredTo && (
              <div className="mt-4 rounded-md bg-[#0F172A] px-3 py-2">
                <p className="text-xs text-[#94A3B8]">Referred to</p>
                <p className="text-sm text-[#F8FAFC]">{report.referredTo}</p>
              </div>
            )}
          </div>
          </FadeIn>
        )}
      </main>

      <Footer />
    </div>
  );
}
