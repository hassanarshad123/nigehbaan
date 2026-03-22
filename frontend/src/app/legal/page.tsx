'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { ExportButton } from '@/components/ui/ExportButton';
import { EmptyState } from '@/components/ui/EmptyState';
import { cn } from '@/lib/utils';
import { Scale, Search, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { fetchCourtJudgments, fetchCourtList, type JudgmentResponse } from '@/lib/api';
import { FadeIn } from '@/components/ui/FadeIn';

const FALLBACK_COURTS = [
  'Lahore High Court',
  'Sindh High Court',
  'Peshawar High Court',
  'Balochistan High Court',
  'Supreme Court of Pakistan',
  'Islamabad High Court',
];
const YEARS = Array.from({ length: 15 }, (_, i) => 2024 - i);
const PPC_SECTIONS = ['364', '364-A', '365', '370', '371', '371-A', '371-B', '374', '377'];
const OUTCOMES = ['convicted', 'acquitted', 'pending', 'dismissed'] as const;
const PAGE_SIZE = 20;

const VERDICT_STYLES: Record<string, string> = {
  convicted: 'bg-[#EF4444]/10 text-[#EF4444]',
  acquitted: 'bg-[#10B981]/10 text-[#10B981]',
  pending: 'bg-[#F59E0B]/10 text-[#F59E0B]',
  dismissed: 'bg-[#94A3B8]/10 text-[#94A3B8]',
};

export default function LegalPage() {
  const { data: courtList } = useQuery({
    queryKey: ['court-list'],
    queryFn: fetchCourtList,
  });
  const COURTS = courtList && courtList.length > 0 ? courtList : FALLBACK_COURTS;

  const [court, setCourt] = useState('');
  const [year, setYear] = useState('');
  const [ppcSection, setPpcSection] = useState('');
  const [outcome, setOutcome] = useState('');
  const [page, setPage] = useState(1);

  const filters = {
    court: court || undefined,
    year: year ? Number(year) : undefined,
    ppcSection: ppcSection || undefined,
    verdict: outcome || undefined,
    page,
    limit: PAGE_SIZE,
  };

  const { data: judgments, isLoading, error } = useQuery({
    queryKey: ['legal', court, year, ppcSection, outcome, page],
    queryFn: () => fetchCourtJudgments(filters),
  });

  const handleFilterChange = () => {
    setPage(1);
  };

  const rows = judgments ?? [];
  const hasMore = rows.length === PAGE_SIZE;
  const hasFilters = court || year || ppcSection || outcome;

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
        {/* Page header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Scale className="h-5 w-5 text-[#F59E0B]" />
              <h1 className="text-2xl font-bold text-[#F8FAFC]">Court Judgments</h1>
            </div>
            <p className="text-sm text-[#94A3B8]">
              Search Pakistan court judgments related to child trafficking and exploitation.
            </p>
          </div>
          <ExportButton table="judgments" params={court ? { court } : undefined} label="Export Judgments" />
        </div>

        {/* Filters */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 mb-6">
          <div className="grid grid-cols-2 gap-3 sm:flex sm:flex-wrap sm:gap-4">
            <div>
              <label className="block text-xs text-[#94A3B8] mb-1">Court</label>
              <select
                value={court}
                onChange={(e) => { setCourt(e.target.value); handleFilterChange(); }}
                className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus transition-default"
              >
                <option value="">All Courts</option>
                {COURTS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-[#94A3B8] mb-1">Year</label>
              <select
                value={year}
                onChange={(e) => { setYear(e.target.value); handleFilterChange(); }}
                className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus transition-default"
              >
                <option value="">All Years</option>
                {YEARS.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-[#94A3B8] mb-1">PPC Section</label>
              <select
                value={ppcSection}
                onChange={(e) => { setPpcSection(e.target.value); handleFilterChange(); }}
                className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus transition-default"
              >
                <option value="">All Sections</option>
                {PPC_SECTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-[#94A3B8] mb-1">Outcome</label>
              <select
                value={outcome}
                onChange={(e) => { setOutcome(e.target.value); handleFilterChange(); }}
                className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus transition-default"
              >
                <option value="">All Outcomes</option>
                {OUTCOMES.map((o) => (
                  <option key={o} value={o} className="capitalize">{o}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Loading state */}
        {isLoading && (
          <>
            {/* Desktop skeleton table */}
            <div className="hidden sm:block rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
              <div className="skeleton h-11 w-full" />
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="flex gap-4 px-4 py-3 border-b border-[#334155]/30">
                  <div className="skeleton h-5 w-32 rounded" />
                  <div className="skeleton h-5 w-24 rounded" />
                  <div className="skeleton h-5 w-20 rounded" />
                  <div className="skeleton h-5 w-16 rounded" />
                  <div className="skeleton h-5 w-20 rounded-full" />
                  <div className="skeleton h-5 w-16 rounded" />
                </div>
              ))}
            </div>
            {/* Mobile skeleton cards */}
            <div className="sm:hidden space-y-2">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="skeleton h-28 rounded-lg" />
              ))}
            </div>
          </>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 px-4 py-8 text-center">
            <p className="text-sm text-[#EF4444]">Failed to load judgments. Please try again.</p>
          </div>
        )}

        {/* Results */}
        {!isLoading && !error && (
          <FadeIn>
            {rows.length === 0 ? (
              <div className="rounded-lg border border-[#334155] bg-[#1E293B]">
                <EmptyState
                  icon={<Search className="h-8 w-8" />}
                  title="No judgments found"
                  description={
                    hasFilters
                      ? 'No judgments match your filters \u2014 try broadening your search.'
                      : 'No court judgment data available yet.'
                  }
                />
              </div>
            ) : (
              <>
                {/* Result count */}
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs text-[#94A3B8]">
                    Showing {(page - 1) * PAGE_SIZE + 1}\u2013{(page - 1) * PAGE_SIZE + rows.length} results
                    {hasMore && '+'}
                  </p>
                  <p className="text-xs text-[#94A3B8] tabular-nums">
                    Page {page}
                  </p>
                </div>

                {/* Desktop table */}
                <div className="hidden sm:block rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-[#334155] text-left">
                          <th className="px-4 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Court</th>
                          <th className="px-4 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Case Number</th>
                          <th className="px-4 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Date</th>
                          <th className="px-4 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wider">PPC Sections</th>
                          <th className="px-4 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Verdict</th>
                          <th className="px-4 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Sentence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((j) => (
                          <tr key={j.id} className="border-b border-[#334155]/50 hover:bg-[#334155]/20 transition-default">
                            <td className="px-4 py-3 text-[#F8FAFC]">{j.courtName}</td>
                            <td className="px-4 py-3">
                              <span className="flex items-center gap-1 text-[#06B6D4]">
                                <FileText className="h-3.5 w-3.5" />
                                {j.caseNumber}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-[#94A3B8] tabular-nums">{j.judgmentDate}</td>
                            <td className="px-4 py-3">
                              <div className="flex gap-1 flex-wrap">
                                {(j.ppcSections ?? []).map((s) => (
                                  <span key={s} className="rounded bg-[#0F172A] px-1.5 py-0.5 text-xs text-[#F8FAFC]">
                                    {s}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium capitalize', VERDICT_STYLES[j.verdict] ?? 'text-[#94A3B8]')}>
                                {j.verdict ?? '-'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-[#F8FAFC] tabular-nums">
                              {j.sentenceYears != null ? `${j.sentenceYears} years` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Mobile card view */}
                <div className="sm:hidden space-y-2">
                  {rows.map((j) => (
                    <div
                      key={j.id}
                      className="rounded-lg border border-[#334155] bg-[#1E293B] p-3"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span className="text-sm font-medium text-[#F8FAFC]">{j.courtName}</span>
                        <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium capitalize shrink-0', VERDICT_STYLES[j.verdict] ?? 'text-[#94A3B8]')}>
                          {j.verdict ?? '-'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-[#06B6D4] text-xs mb-2">
                        <FileText className="h-3 w-3" />
                        {j.caseNumber}
                      </div>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                        <div>
                          <span className="text-[#94A3B8]">Date: </span>
                          <span className="text-[#F8FAFC] tabular-nums">{j.judgmentDate}</span>
                        </div>
                        <div>
                          <span className="text-[#94A3B8]">Sentence: </span>
                          <span className="text-[#F8FAFC] tabular-nums">
                            {j.sentenceYears != null ? `${j.sentenceYears} yrs` : '-'}
                          </span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-[#94A3B8]">PPC: </span>
                          {(j.ppcSections ?? []).map((s) => (
                            <span key={s} className="rounded bg-[#0F172A] px-1.5 py-0.5 text-xs text-[#F8FAFC] mr-1">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-center gap-3 mt-6">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className={cn(
                      'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-default',
                      page === 1
                        ? 'text-[#334155] cursor-not-allowed'
                        : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
                    )}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </button>
                  <span className="text-sm text-[#94A3B8] tabular-nums">Page {page}</span>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!hasMore}
                    className={cn(
                      'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-default',
                      !hasMore
                        ? 'text-[#334155] cursor-not-allowed'
                        : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
                    )}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </>
            )}
          </FadeIn>
        )}
      </main>

      <Footer />
    </div>
  );
}
