'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { RiskGauge } from '@/components/district/RiskGauge';
import { DistrictStats } from '@/components/district/DistrictStats';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { fetchDistrictProfile, fetchDistrictIncidents } from '@/lib/api';

const DistrictMap = dynamic(
  () => import('@/components/district/DistrictMap').then((mod) => mod.DistrictMap),
  { ssr: false },
);

interface DistrictPageProps {
  params: { pcode: string };
}

export default function DistrictPage({ params }: DistrictPageProps) {
  const { pcode } = params;

  const { data: district, isLoading: profileLoading, error: profileError } = useQuery({
    queryKey: ['district', pcode],
    queryFn: () => fetchDistrictProfile(pcode),
  });

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['district-incidents', pcode],
    queryFn: () => fetchDistrictIncidents(pcode, 10),
  });

  if (profileLoading) {
    return (
      <div className="min-h-screen bg-[#0F172A]">
        <Header />
        <main className="flex items-center justify-center pt-32">
          <Loader2 className="h-8 w-8 animate-spin text-[#06B6D4]" />
        </main>
      </div>
    );
  }

  if (profileError || !district) {
    return (
      <div className="min-h-screen bg-[#0F172A]">
        <Header />
        <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
          <div className="mb-6">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-sm text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Map
            </Link>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-8 text-center">
            <p className="text-[#94A3B8]">District not found for PCODE: {pcode}</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const timelineData = timeline ?? [];
  const maxCount = timelineData.length > 0 ? Math.max(...timelineData.map((e) => e.count)) : 1;

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Map
          </Link>
        </div>

        {/* District header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[#F8FAFC]">{district.nameEn}</h1>
            <p className="font-urdu text-lg text-[#94A3B8]">{district.nameUr}</p>
            <p className="text-xs text-[#334155] mt-1">PCODE: {pcode}</p>
          </div>
          <RiskGauge score={district.vulnerability ?? 0} />
        </div>

        {/* Stats grid */}
        <div className="mb-8">
          <DistrictStats
            population={district.population ?? 0}
            incidentCount={district.incidents}
            kilnCount={district.kilnCount}
            schoolCount={0}
            convictionRate={district.convictionRate ?? 0}
          />
        </div>

        {/* Map and timeline side-by-side */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
          {/* District map */}
          <div>
            <h2 className="text-sm font-semibold text-[#F8FAFC] mb-3">
              District Map
            </h2>
            <DistrictMap
              latitude={district.centroidLat ?? 30.3753}
              longitude={district.centroidLon ?? 69.3451}
            />
          </div>

          {/* Incident timeline */}
          <div>
            <h2 className="text-sm font-semibold text-[#F8FAFC] mb-3">
              Incident Timeline
            </h2>
            <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
              {timelineLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
                </div>
              ) : timelineData.length === 0 ? (
                <p className="text-sm text-[#94A3B8] text-center py-8">No incident data available</p>
              ) : (
                <div className="space-y-2">
                  {timelineData.map((entry) => {
                    const widthPct = (entry.count / maxCount) * 100;
                    return (
                      <div key={entry.year} className="flex items-center gap-3">
                        <span className="text-xs text-[#94A3B8] w-10 text-right tabular-nums">
                          {entry.year}
                        </span>
                        <div className="flex-1 h-5 bg-[#0F172A] rounded overflow-hidden">
                          <div
                            className="h-full rounded bg-[#06B6D4]/60 transition-all duration-500"
                            style={{ width: `${widthPct}%` }}
                          />
                        </div>
                        <span className="text-xs text-[#F8FAFC] w-10 tabular-nums">
                          {entry.count}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
