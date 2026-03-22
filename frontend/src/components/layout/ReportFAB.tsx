'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AlertTriangle } from 'lucide-react';

export function ReportFAB() {
  const pathname = usePathname();

  // Hide on report pages (user is already there)
  if (pathname.startsWith('/report')) return null;

  return (
    <Link
      href="/report"
      aria-label="Report a child in danger"
      className="fixed bottom-6 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-[#F59E0B] shadow-lg shadow-[#F59E0B]/25 transition-all duration-200 hover:scale-110 hover:shadow-xl hover:shadow-[#F59E0B]/30 active:scale-95 animate-pulse-slow safe-bottom"
    >
      <AlertTriangle className="h-6 w-6 text-[#0F172A]" />
    </Link>
  );
}
