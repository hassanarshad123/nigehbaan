'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { SummaryCards } from '@/components/dashboard/SummaryCards';
import { TrendChart } from '@/components/dashboard/TrendChart';
import { ProvinceComparison } from '@/components/dashboard/ProvinceComparison';
import { CaseTypeBreakdown } from '@/components/dashboard/CaseTypeBreakdown';
import { ConvictionRates } from '@/components/dashboard/ConvictionRates';
import { FilterControls } from '@/components/dashboard/FilterControls';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-2xl px-4 pt-16 pb-8">
        {/* Page title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[#F8FAFC]">
            Analytics Dashboard
          </h1>
          <p className="text-sm text-[#94A3B8] mt-1">
            Pakistan child trafficking intelligence — aggregated from 12 data sources
          </p>
        </div>

        {/* Filter controls */}
        <div className="mb-6">
          <FilterControls />
        </div>

        {/* Summary KPI cards */}
        <div className="mb-6">
          <SummaryCards />
        </div>

        {/* Charts grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <TrendChart />
          <ProvinceComparison />
          <CaseTypeBreakdown />
          <ConvictionRates />
        </div>
      </main>

      <Footer />
    </div>
  );
}
