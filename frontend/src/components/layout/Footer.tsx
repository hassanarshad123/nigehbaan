'use client';

import React from 'react';
import Link from 'next/link';
import { Phone } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-[#334155] bg-[#0F172A] px-4 py-6">
      <div className="mx-auto max-w-screen-2xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          {/* Helplines */}
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5 text-[#94A3B8]">
              <Phone className="h-4 w-4 text-[#EF4444]" />
              Emergency Helplines:
            </span>
            <a
              href="tel:1099"
              className="rounded bg-[#1E293B] px-2 py-0.5 text-[#F8FAFC] hover:bg-[#334155] transition-default"
            >
              Child Protection: 1099
            </a>
            <a
              href="tel:1098"
              className="rounded bg-[#1E293B] px-2 py-0.5 text-[#F8FAFC] hover:bg-[#334155] transition-default"
            >
              Edhi: 1098
            </a>
            <a
              href="tel:080022444"
              className="rounded bg-[#1E293B] px-2 py-0.5 text-[#F8FAFC] hover:bg-[#334155] transition-default"
            >
              Roshni: 0800-22444
            </a>
          </div>

          {/* Links and copyright */}
          <div className="flex items-center gap-4 text-xs text-[#94A3B8]">
            <Link href="/about" className="hover:text-[#F8FAFC] transition-default">
              About
            </Link>
            <span>|</span>
            <span>Nigehbaan Project — Open Source Intelligence for Child Protection</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
