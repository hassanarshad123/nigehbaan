'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AlertTriangle, Phone, X } from 'lucide-react';

const STORAGE_KEY = 'nigehbaan-banner-dismissed';
const REPORT_PATHS = ['/report', '/report/track', '/report/success'];

export function EmergencyBanner() {
  const pathname = usePathname();
  const [dismissed, setDismissed] = useState(true); // start hidden to avoid flash
  const [mounted, setMounted] = useState(false);

  const isReportPage = REPORT_PATHS.some((p) => pathname.startsWith(p));

  useEffect(() => {
    setMounted(true);
    if (isReportPage) {
      // Always show on report pages
      setDismissed(false);
      return;
    }
    const stored = localStorage.getItem(STORAGE_KEY);
    setDismissed(stored === 'true');
  }, [isReportPage]);

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem(STORAGE_KEY, 'true');
  };

  if (!mounted || dismissed) return null;

  // Don't show on map homepage — it has its own full-screen experience
  if (pathname === '/') return null;

  return (
    <div
      role="alert"
      className="sticky top-12 z-40 border-b border-[#EF4444]/20 bg-[#EF4444]/5 backdrop-blur-sm"
    >
      <div className="mx-auto flex max-w-screen-2xl items-center justify-between gap-3 px-4 py-2">
        <div className="flex items-center gap-3 text-xs sm:text-sm">
          <AlertTriangle className="h-4 w-4 text-[#EF4444] shrink-0" />
          <span className="text-[#F8FAFC]">
            See a child in danger?
          </span>
          <Link
            href="/report"
            className="font-semibold text-[#F59E0B] hover:underline"
          >
            Report it now
          </Link>
          <span className="hidden sm:inline text-[#94A3B8]">|</span>
          <a
            href="tel:1099"
            className="hidden sm:inline-flex items-center gap-1 text-[#EF4444] hover:underline"
          >
            <Phone className="h-3 w-3" />
            1099
          </a>
        </div>
        {!isReportPage && (
          <button
            onClick={handleDismiss}
            className="shrink-0 rounded p-1 text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
            aria-label="Dismiss emergency banner"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
