'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { CheckCircle2, Phone, ArrowLeft } from 'lucide-react';

export default function ReportSuccessPage() {
  // In production this would come from the API response / URL params
  const referenceNumber = `NGH-${Date.now().toString(36).toUpperCase()}`;

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-lg px-4 pt-24 pb-8 text-center">
        {/* Success icon */}
        <div className="mb-6 flex justify-center">
          <div className="rounded-full bg-[#10B981]/10 p-4">
            <CheckCircle2 className="h-12 w-12 text-[#10B981]" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-[#F8FAFC] mb-2">
          Report Submitted
        </h1>
        <p className="text-sm text-[#94A3B8] mb-6">
          Your report has been received and will be reviewed by trained personnel.
          A reference number has been assigned.
        </p>

        {/* Reference number */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 mb-8">
          <p className="text-xs text-[#94A3B8] mb-1">Reference Number</p>
          <p className="text-xl font-mono font-bold text-[#06B6D4] tracking-wider">
            {referenceNumber}
          </p>
          <p className="text-xs text-[#94A3B8] mt-2">
            Save this number for future reference
          </p>
        </div>

        {/* Emergency helplines */}
        <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 p-4 mb-8 text-left">
          <div className="flex items-center gap-2 mb-3">
            <Phone className="h-4 w-4 text-[#EF4444]" />
            <p className="text-sm font-medium text-[#F8FAFC]">
              If a child is in immediate danger, call:
            </p>
          </div>
          <div className="space-y-2">
            <a
              href="tel:1099"
              className="flex items-center justify-between rounded-md bg-[#0F172A] px-3 py-2 text-sm hover:bg-[#334155] transition-default"
            >
              <span className="text-[#F8FAFC]">Child Protection Helpline</span>
              <span className="font-mono font-bold text-[#EF4444]">1099</span>
            </a>
            <a
              href="tel:1098"
              className="flex items-center justify-between rounded-md bg-[#0F172A] px-3 py-2 text-sm hover:bg-[#334155] transition-default"
            >
              <span className="text-[#F8FAFC]">Edhi Foundation</span>
              <span className="font-mono font-bold text-[#EF4444]">1098</span>
            </a>
            <a
              href="tel:080022444"
              className="flex items-center justify-between rounded-md bg-[#0F172A] px-3 py-2 text-sm hover:bg-[#334155] transition-default"
            >
              <span className="text-[#F8FAFC]">Roshni Helpline</span>
              <span className="font-mono font-bold text-[#EF4444]">0800-22444</span>
            </a>
          </div>
        </div>

        {/* Back to map */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-md bg-[#06B6D4] px-5 py-2.5 text-sm font-medium text-[#0F172A] hover:bg-[#06B6D4]/90 transition-default"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Map
        </Link>
      </main>

      <Footer />
    </div>
  );
}
