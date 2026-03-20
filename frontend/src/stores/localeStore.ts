import { create } from 'zustand';

type Locale = 'en' | 'ur';

interface LocaleState {
  locale: Locale;
  mounted: boolean;
  setLocale: (locale: Locale) => void;
  setMounted: () => void;
}

function getStoredLocale(): Locale {
  if (typeof window === 'undefined') return 'en';
  const stored = localStorage.getItem('nigehbaan-locale');
  return stored === 'ur' ? 'ur' : 'en';
}

export const useLocaleStore = create<LocaleState>((set) => ({
  locale: 'en',
  mounted: false,
  setLocale: (locale) => {
    localStorage.setItem('nigehbaan-locale', locale);
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === 'ur' ? 'rtl' : 'ltr';
    set({ locale });
  },
  setMounted: () => {
    const locale = getStoredLocale();
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === 'ur' ? 'rtl' : 'ltr';
    set({ locale, mounted: true });
  },
}));
