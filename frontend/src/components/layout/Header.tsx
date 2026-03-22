'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { LanguageToggle } from './LanguageToggle';
import { Map, BarChart3, FileWarning, Scale, LifeBuoy, Info, Activity, Menu, X, GitCompareArrows, Newspaper } from 'lucide-react';

interface NavItem {
  href: string;
  labelKey: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/', labelKey: 'map', icon: <Map className="h-4 w-4" /> },
  { href: '/dashboard', labelKey: 'dashboard', icon: <BarChart3 className="h-4 w-4" /> },
  { href: '/report', labelKey: 'report', icon: <FileWarning className="h-4 w-4" /> },
  { href: '/legal', labelKey: 'legal', icon: <Scale className="h-4 w-4" /> },
  { href: '/news', labelKey: 'news', icon: <Newspaper className="h-4 w-4" /> },
  { href: '/compare', labelKey: 'compare', icon: <GitCompareArrows className="h-4 w-4" /> },
  { href: '/scrapers', labelKey: 'scrapers', icon: <Activity className="h-4 w-4" /> },
  { href: '/resources', labelKey: 'resources', icon: <LifeBuoy className="h-4 w-4" /> },
  { href: '/about', labelKey: 'about', icon: <Info className="h-4 w-4" /> },
];

function isActive(pathname: string, href: string): boolean {
  if (href === '/') return pathname === '/';
  return pathname.startsWith(href);
}

export function Header() {
  const t = useTranslations('nav');
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 bg-glass border-b border-[#334155]/50">
        <div className="mx-auto flex h-12 max-w-screen-2xl items-center justify-between px-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="font-urdu text-lg text-[#06B6D4]">نگہبان</span>
            <span className="text-sm font-semibold tracking-wide text-[#F8FAFC]">
              Nigehbaan
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm',
                    'transition-default',
                    active
                      ? 'text-[#F8FAFC] bg-[#1E293B] border-b-2 border-[#06B6D4]'
                      : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
                  )}
                >
                  {item.icon}
                  <span>{t(item.labelKey)}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2">
            <LanguageToggle />
            {/* Mobile hamburger */}
            <button
              onClick={() => setIsMenuOpen((v) => !v)}
              className="md:hidden flex items-center justify-center h-11 w-11 rounded-md text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B] transition-default"
              aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
            >
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile drawer */}
        <div
          className={cn(
            'md:hidden overflow-hidden transition-all duration-300 ease-in-out border-t border-[#334155]/50',
            isMenuOpen ? 'max-h-[420px]' : 'max-h-0 border-t-transparent',
          )}
        >
          <nav className="bg-glass px-4 py-2">
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMenuOpen(false)}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'flex items-center gap-2.5 rounded-md px-3 py-2.5 text-sm',
                    'transition-default',
                    active
                      ? 'text-[#F8FAFC] bg-[#1E293B] border-l-2 border-[#06B6D4]'
                      : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
                  )}
                >
                  {item.icon}
                  <span>{t(item.labelKey)}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Backdrop overlay */}
      {isMenuOpen && (
        <div
          className="fixed inset-0 z-[45] bg-black/30 md:hidden"
          onClick={() => setIsMenuOpen(false)}
        />
      )}
    </>
  );
}
