'use client';

import React from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { Phone, RotateCcw } from 'lucide-react';
import { useWelcomeStore } from '@/stores/welcomeStore';

export function Footer() {
  const t = useTranslations('footer');
  const resetWelcome = useWelcomeStore((s) => s.resetWelcome);

  return (
    <footer className="border-t border-[#334155] bg-[#0F172A] px-4 py-6">
      <div className="mx-auto max-w-screen-2xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          {/* Helplines */}
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5 text-[#94A3B8]">
              <Phone className="h-4 w-4 text-[#EF4444]" />
              {t('emergency')}:
            </span>
            <a
              href="tel:1099"
              className="rounded bg-[#1E293B] px-2 py-0.5 text-[#F8FAFC] hover:bg-[#334155] transition-default"
            >
              {t('childProtection')}
            </a>
            <a
              href="tel:1098"
              className="rounded bg-[#1E293B] px-2 py-0.5 text-[#F8FAFC] hover:bg-[#334155] transition-default"
            >
              {t('edhi')}
            </a>
            <a
              href="tel:080022444"
              className="rounded bg-[#1E293B] px-2 py-0.5 text-[#F8FAFC] hover:bg-[#334155] transition-default"
            >
              {t('roshni')}
            </a>
          </div>

          {/* Links and copyright */}
          <div className="flex items-center gap-4 text-xs text-[#94A3B8]">
            <button
              onClick={resetWelcome}
              className="flex items-center gap-1 hover:text-[#F8FAFC] transition-default"
            >
              <RotateCcw className="h-3 w-3" />
              Replay Intro
            </button>
            <span>|</span>
            <Link href="/about" className="hover:text-[#F8FAFC] transition-default">
              {t('about')}
            </Link>
            <span>|</span>
            <span>{t('copyright')}</span>
          </div>
        </div>
        <p className="text-center text-xs text-[#64748B] mt-4 md:mt-0">
          Made with love by Hassan
        </p>
      </div>
    </footer>
  );
}
