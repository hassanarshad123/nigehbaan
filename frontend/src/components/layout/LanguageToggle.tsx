'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Globe } from 'lucide-react';

export function LanguageToggle() {
  const [locale, setLocale] = useState<'en' | 'ur'>('en');

  const toggle = () => {
    const next = locale === 'en' ? 'ur' : 'en';
    setLocale(next);
    // In production this would trigger next-intl locale switch
    document.documentElement.lang = next;
    document.documentElement.dir = next === 'ur' ? 'rtl' : 'ltr';
  };

  return (
    <button
      onClick={toggle}
      className={cn(
        'flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm',
        'border border-[#334155] text-[#94A3B8]',
        'hover:border-[#06B6D4] hover:text-[#F8FAFC]',
        'transition-default',
      )}
      aria-label="Toggle language"
    >
      <Globe className="h-3.5 w-3.5" />
      <span>{locale === 'en' ? 'اردو' : 'EN'}</span>
    </button>
  );
}
