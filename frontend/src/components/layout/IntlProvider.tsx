'use client';

import React, { useEffect, useState, type ReactNode } from 'react';
import { NextIntlClientProvider, type AbstractIntlMessages } from 'next-intl';

// Static imports for both message files
import enMessages from '../../../messages/en.json';
import urMessages from '../../../messages/ur.json';

const MESSAGES: Record<string, AbstractIntlMessages> = {
  en: enMessages,
  ur: urMessages,
};

function getStoredLocale(): 'en' | 'ur' {
  if (typeof window === 'undefined') return 'en';
  const stored = localStorage.getItem('nigehbaan-locale');
  return stored === 'ur' ? 'ur' : 'en';
}

export function IntlProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<'en' | 'ur'>('en');

  useEffect(() => {
    setLocale(getStoredLocale());
  }, []);

  // Listen for locale change events dispatched by LanguageToggle
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ locale: 'en' | 'ur' }>).detail;
      setLocale(detail.locale);
      document.documentElement.lang = detail.locale;
      document.documentElement.dir = detail.locale === 'ur' ? 'rtl' : 'ltr';
    };
    window.addEventListener('locale-change', handler);
    return () => window.removeEventListener('locale-change', handler);
  }, []);

  return (
    <NextIntlClientProvider locale={locale} messages={MESSAGES[locale]} timeZone="Asia/Karachi">
      {children}
    </NextIntlClientProvider>
  );
}
