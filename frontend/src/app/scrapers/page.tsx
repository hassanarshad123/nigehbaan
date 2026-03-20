'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { ScraperSummaryCards } from '@/components/scrapers/ScraperSummaryCards';
import { ScraperTable } from '@/components/scrapers/ScraperTable';

export default function ScrapersPage() {
  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-2xl px-4 pt-16 pb-8">
        {/* Page title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[#F8FAFC]">
            Scrapers Health
          </h1>
          <p className="text-sm text-[#94A3B8] mt-1">
            Real-time monitoring of all data collection scrapers
          </p>
        </div>

        {/* Summary KPI cards */}
        <div className="mb-6">
          <ScraperSummaryCards />
        </div>

        {/* Scraper status table */}
        <ScraperTable />
      </main>

      <Footer />
    </div>
  );
}
