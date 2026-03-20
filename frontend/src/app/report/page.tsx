'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { ReportForm } from '@/components/report/ReportForm';
import { ShieldCheck, Phone } from 'lucide-react';

export default function ReportPage() {
  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-2xl px-4 pt-16 pb-8">
        {/* Page header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-[#F8FAFC] mb-2">
            Submit a Report
          </h1>
          <p className="text-sm text-[#94A3B8] max-w-lg mx-auto">
            Report suspicious activity or a child in danger. You can report
            anonymously. All reports are reviewed by trained personnel.
          </p>
        </div>

        {/* Safety banner */}
        <div className="mx-auto max-w-2xl mb-8 rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 p-4">
          <div className="flex items-start gap-3">
            <Phone className="h-5 w-5 text-[#EF4444] shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-[#F8FAFC] mb-1">
                If a child is in immediate danger, call now:
              </p>
              <div className="flex flex-wrap gap-3 text-sm">
                <a href="tel:1099" className="text-[#EF4444] hover:underline">
                  Child Protection: 1099
                </a>
                <a href="tel:1098" className="text-[#EF4444] hover:underline">
                  Edhi: 1098
                </a>
                <a href="tel:080022444" className="text-[#EF4444] hover:underline">
                  Roshni: 0800-22444
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Privacy assurance */}
        <div className="mx-auto max-w-2xl mb-6 flex items-center gap-2 text-xs text-[#94A3B8]">
          <ShieldCheck className="h-4 w-4 text-[#10B981]" />
          <span>Your report is encrypted. Anonymous reporting is enabled by default.</span>
        </div>

        {/* Report form */}
        <ReportForm />
      </main>

      <Footer />
    </div>
  );
}
