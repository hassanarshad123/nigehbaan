'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { useQueries } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { DistrictSelector } from '@/components/compare/DistrictSelector';
import { ComparisonTable } from '@/components/compare/ComparisonTable';
import { EmptyState } from '@/components/ui/EmptyState';
import { GitCompareArrows, Loader2 } from 'lucide-react';
import { fetchDistrictProfile, fetchVulnerability, type DistrictVulnerability } from '@/lib/api';

const ComparisonRadarChart = dynamic(
  () => import('@/components/compare/RadarChart').then((m) => m.ComparisonRadarChart),
  { ssr: false },
);

export default function ComparePage() {
  const [selectedPcodes, setSelectedPcodes] = useState<string[]>([]);

  const profileQueries = useQueries({
    queries: selectedPcodes.map((pcode) => ({
      queryKey: ['district', pcode],
      queryFn: () => fetchDistrictProfile(pcode),
      staleTime: 5 * 60_000,
    })),
  });

  const vulnQueries = useQueries({
    queries: selectedPcodes.map((pcode) => ({
      queryKey: ['district-vulnerability', pcode],
      queryFn: () => fetchVulnerability(pcode),
      staleTime: 5 * 60_000,
    })),
  });

  const isLoading = profileQueries.some((q) => q.isLoading) || vulnQueries.some((q) => q.isLoading);

  const districts = selectedPcodes
    .map((pcode, i) => {
      const profile = profileQueries[i]?.data;
      const vuln = vulnQueries[i]?.data;
      if (!profile || !vuln) return null;
      return {
        pcode,
        nameEn: profile.nameEn,
        vulnerability: vuln,
      };
    })
    .filter((d): d is NonNullable<typeof d> => d != null);

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
        {/* Page header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <GitCompareArrows className="h-5 w-5 text-[#06B6D4]" />
            <h1 className="text-2xl font-bold text-[#F8FAFC]">District Comparison</h1>
          </div>
          <p className="text-sm text-[#94A3B8]">
            Compare vulnerability indicators across 2-4 districts side by side.
          </p>
        </div>

        {/* District selector */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 mb-6">
          <label className="block text-xs text-[#94A3B8] mb-2">Select Districts to Compare</label>
          <DistrictSelector
            selected={selectedPcodes}
            onChange={setSelectedPcodes}
            max={4}
          />
        </div>

        {/* Loading */}
        {isLoading && selectedPcodes.length > 0 && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-[#06B6D4]" />
          </div>
        )}

        {/* Empty state */}
        {selectedPcodes.length === 0 && (
          <div className="rounded-lg border border-[#334155] bg-[#1E293B]">
            <EmptyState
              icon={<GitCompareArrows className="h-10 w-10" />}
              title="Select districts to compare"
              description="Choose 2-4 districts above to see their vulnerability indicators overlaid on a radar chart."
            />
          </div>
        )}

        {/* Charts and table */}
        {!isLoading && districts.length >= 2 && (
          <div className="space-y-6">
            <ComparisonRadarChart districts={districts} />
            <ComparisonTable districts={districts} />
          </div>
        )}

        {/* Only 1 selected */}
        {!isLoading && selectedPcodes.length === 1 && districts.length === 1 && (
          <div className="rounded-lg border border-[#334155] bg-[#1E293B]">
            <EmptyState
              icon={<GitCompareArrows className="h-10 w-10" />}
              title="Select at least one more district"
              description="Add another district to start comparing vulnerability indicators."
            />
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
