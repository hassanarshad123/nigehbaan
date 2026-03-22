'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { SummaryCards } from '@/components/dashboard/SummaryCards';
import { FilterControls } from '@/components/dashboard/FilterControls';
import { ExportButton } from '@/components/ui/ExportButton';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

const TrendChart = dynamic(
  () => import('@/components/dashboard/TrendChart').then((m) => m.TrendChart),
  { ssr: false },
);
const ProvinceComparison = dynamic(
  () => import('@/components/dashboard/ProvinceComparison').then((m) => m.ProvinceComparison),
  { ssr: false },
);
const CaseTypeBreakdown = dynamic(
  () => import('@/components/dashboard/CaseTypeBreakdown').then((m) => m.CaseTypeBreakdown),
  { ssr: false },
);
const ConvictionRates = dynamic(
  () => import('@/components/dashboard/ConvictionRates').then((m) => m.ConvictionRates),
  { ssr: false },
);
const StatisticalReports = dynamic(
  () => import('@/components/dashboard/StatisticalReports').then((m) => m.StatisticalReports),
  { ssr: false },
);
const TransparencyMetrics = dynamic(
  () => import('@/components/dashboard/TransparencyMetrics').then((m) => m.TransparencyMetrics),
  { ssr: false },
);
const TipReportTimeline = dynamic(
  () => import('@/components/dashboard/TipReportTimeline').then((m) => m.TipReportTimeline),
  { ssr: false },
);

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-2xl px-4 pt-16 pb-8">
        {/* Page title */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#F8FAFC]">
              Analytics Dashboard
            </h1>
            <p className="text-sm text-[#94A3B8] mt-1">
              Pakistan child trafficking intelligence \u2014 aggregated from 32 data sources
            </p>
          </div>
          <ExportButton table="incidents" label="Export Incidents" />
        </div>

        {/* Filter controls */}
        <div className="mb-6">
          <FilterControls />
        </div>

        {/* Summary KPI cards */}
        <div className="mb-6">
          <SummaryCards />
        </div>

        {/* Charts grid — each wrapped in its own error boundary */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ErrorBoundary>
            <TrendChart />
          </ErrorBoundary>
          <ErrorBoundary>
            <ProvinceComparison />
          </ErrorBoundary>
          <ErrorBoundary>
            <CaseTypeBreakdown />
          </ErrorBoundary>
          <ErrorBoundary>
            <ConvictionRates />
          </ErrorBoundary>
        </div>

        {/* Extended data sections */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mt-6">
          <ErrorBoundary>
            <StatisticalReports />
          </ErrorBoundary>
          <ErrorBoundary>
            <TransparencyMetrics />
          </ErrorBoundary>
          <ErrorBoundary>
            <TipReportTimeline />
          </ErrorBoundary>
        </div>
      </main>

      <Footer />
    </div>
  );
}
