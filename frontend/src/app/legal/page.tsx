'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { cn } from '@/lib/utils';
import { Scale, Search, FileText } from 'lucide-react';

interface JudgmentRow {
  id: string;
  courtName: string;
  caseNumber: string;
  judgmentDate: string;
  ppcSections: string[];
  verdict: 'convicted' | 'acquitted' | 'pending' | 'dismissed';
  sentenceYears: number | null;
}

// Mock judgments data
const MOCK_JUDGMENTS: JudgmentRow[] = [
  {
    id: '1',
    courtName: 'Lahore High Court',
    caseNumber: 'Crl.A. No. 1234/2023',
    judgmentDate: '2023-11-15',
    ppcSections: ['364-A', '371-A'],
    verdict: 'convicted',
    sentenceYears: 14,
  },
  {
    id: '2',
    courtName: 'Supreme Court',
    caseNumber: 'Crl.P. No. 567/2023',
    judgmentDate: '2023-09-22',
    ppcSections: ['364-A'],
    verdict: 'convicted',
    sentenceYears: 10,
  },
  {
    id: '3',
    courtName: 'Sindh High Court',
    caseNumber: 'Crl.A. No. 890/2023',
    judgmentDate: '2023-07-10',
    ppcSections: ['371-B', '374'],
    verdict: 'acquitted',
    sentenceYears: null,
  },
  {
    id: '4',
    courtName: 'Peshawar High Court',
    caseNumber: 'Crl.A. No. 321/2024',
    judgmentDate: '2024-02-18',
    ppcSections: ['364-A', '377'],
    verdict: 'convicted',
    sentenceYears: 7,
  },
  {
    id: '5',
    courtName: 'Islamabad Sessions Court',
    caseNumber: 'Case No. 456/2024',
    judgmentDate: '2024-01-05',
    ppcSections: ['371-A'],
    verdict: 'pending',
    sentenceYears: null,
  },
];

const COURTS = ['Lahore High Court', 'Sindh High Court', 'Peshawar High Court', 'Balochistan High Court', 'Supreme Court', 'Islamabad Sessions Court'];
const YEARS = Array.from({ length: 15 }, (_, i) => 2024 - i);
const PPC_SECTIONS = ['364-A', '371-A', '371-B', '374', '377'];
const OUTCOMES = ['convicted', 'acquitted', 'pending', 'dismissed'] as const;

const VERDICT_STYLES: Record<string, string> = {
  convicted: 'bg-[#EF4444]/10 text-[#EF4444]',
  acquitted: 'bg-[#10B981]/10 text-[#10B981]',
  pending: 'bg-[#F59E0B]/10 text-[#F59E0B]',
  dismissed: 'bg-[#94A3B8]/10 text-[#94A3B8]',
};

export default function LegalPage() {
  const [court, setCourt] = useState('');
  const [year, setYear] = useState('');
  const [ppcSection, setPpcSection] = useState('');
  const [outcome, setOutcome] = useState('');

  const filtered = MOCK_JUDGMENTS.filter((j) => {
    if (court && j.courtName !== court) return false;
    if (year && !j.judgmentDate.startsWith(year)) return false;
    if (ppcSection && !j.ppcSections.includes(ppcSection)) return false;
    if (outcome && j.verdict !== outcome) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
        {/* Page header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <Scale className="h-5 w-5 text-[#F59E0B]" />
            <h1 className="text-2xl font-bold text-[#F8FAFC]">Court Judgments</h1>
          </div>
          <p className="text-sm text-[#94A3B8]">
            Search Pakistan court judgments related to child trafficking and exploitation.
          </p>
        </div>

        {/* Filters */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            <div className="min-w-[180px]">
              <label className="block text-xs text-[#94A3B8] mb-1">Court</label>
              <select
                value={court}
                onChange={(e) => setCourt(e.target.value)}
                className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus transition-default"
              >
                <option value="">All Courts</option>
                {COURTS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="min-w-[120px]">
              <label className="block text-xs text-[#94A3B8] mb-1">Year</label>
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus transition-default"
              >
                <option value="">All Years</option>
                {YEARS.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div className="min-w-[140px]">
              <label className="block text-xs text-[#94A3B8] mb-1">PPC Section</label>
              <select
                value={ppcSection}
                onChange={(e) => setPpcSection(e.target.value)}
                className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus transition-default"
              >
                <option value="">All Sections</option>
                {PPC_SECTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="min-w-[140px]">
              <label className="block text-xs text-[#94A3B8] mb-1">Outcome</label>
              <select
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
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

        {/* Results table */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
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
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-[#94A3B8]">
                      <Search className="mx-auto h-6 w-6 mb-2 opacity-50" />
                      No judgments found matching your filters.
                    </td>
                  </tr>
                ) : (
                  filtered.map((j) => (
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
                        <div className="flex gap-1">
                          {j.ppcSections.map((s) => (
                            <span key={s} className="rounded bg-[#0F172A] px-1.5 py-0.5 text-xs text-[#F8FAFC]">
                              {s}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium capitalize', VERDICT_STYLES[j.verdict])}>
                          {j.verdict}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[#F8FAFC] tabular-nums">
                        {j.sentenceYears != null ? `${j.sentenceYears} years` : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
