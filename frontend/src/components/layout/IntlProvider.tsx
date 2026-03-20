'use client';

import React, { useEffect, type ReactNode } from 'react';
import { NextIntlClientProvider, type AbstractIntlMessages } from 'next-intl';
import { useLocaleStore } from '@/stores/localeStore';

import enMessages from '../../../messages/en.json';
import urMessages from '../../../messages/ur.json';

const MESSAGES: Record<string, AbstractIntlMessages> = {
  en: enMessages,
  ur: urMessages,
};

export function IntlProvider({ children }: { children: ReactNode }) {
  const locale = useLocaleStore((s) => s.locale);
  const mounted = useLocaleStore((s) => s.mounted);
  const setMounted = useLocaleStore((s) => s.setMounted);

  useEffect(() => {
    setMounted();
  }, [setMounted]);

  if (!mounted) {
    return null;
  }

  return (
    <NextIntlClientProvider locale={locale} messages={MESSAGES[locale]} timeZone="Asia/Karachi">
      {children}
    </NextIntlClientProvider>
  );
}
