'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { LanguageToggle } from './LanguageToggle';
import {
  Map,
  BarChart3,
  AlertTriangle,
  Scale,
  Newspaper,
  GitCompareArrows,
  LifeBuoy,
  Info,
  Activity,
  Menu,
  X,
  ChevronDown,
  ChevronRight,
  User,
} from 'lucide-react';

/* ── Types ── */

interface NavLink {
  href: string;
  labelKey: string;
  icon: React.ReactNode;
}

interface NavDropdown {
  labelKey: string;
  icon: React.ReactNode;
  children: NavLink[];
}

type NavItem = NavLink | NavDropdown;

function isDropdown(item: NavItem): item is NavDropdown {
  return 'children' in item;
}

/* ── Navigation config ── */

const NAV_ITEMS: NavItem[] = [
  { href: '/', labelKey: 'map', icon: <Map className="h-4 w-4" /> },
  { href: '/dashboard', labelKey: 'dashboard', icon: <BarChart3 className="h-4 w-4" /> },
  {
    labelKey: 'explore',
    icon: <Scale className="h-4 w-4" />,
    children: [
      { href: '/legal', labelKey: 'courtJudgments', icon: <Scale className="h-4 w-4" /> },
      { href: '/news', labelKey: 'newsMonitor', icon: <Newspaper className="h-4 w-4" /> },
      { href: '/compare', labelKey: 'districtComparison', icon: <GitCompareArrows className="h-4 w-4" /> },
    ],
  },
  {
    labelKey: 'more',
    icon: <Info className="h-4 w-4" />,
    children: [
      { href: '/resources', labelKey: 'resourcesHelplines', icon: <LifeBuoy className="h-4 w-4" /> },
      { href: '/about', labelKey: 'aboutNigehbaan', icon: <Info className="h-4 w-4" /> },
      { href: '/maker', labelKey: 'maker', icon: <User className="h-4 w-4" /> },
      { href: '/scrapers', labelKey: 'scraperCenter', icon: <Activity className="h-4 w-4" /> },
    ],
  },
];

function isActive(pathname: string, href: string): boolean {
  if (href === '/') return pathname === '/';
  return pathname.startsWith(href);
}

function isGroupActive(pathname: string, children: NavLink[]): boolean {
  return children.some((c) => isActive(pathname, c.href));
}

/* ── Desktop dropdown ── */

function DesktopDropdown({ item, pathname, t }: { item: NavDropdown; pathname: string; t: (key: string) => string }) {
  const [open, setOpen] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  const handleEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setOpen(true);
  };
  const handleLeave = () => {
    timeoutRef.current = setTimeout(() => setOpen(false), 150);
  };

  useEffect(() => () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); }, []);

  const active = isGroupActive(pathname, item.children);

  return (
    <div ref={ref} className="relative" onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="true"
        className={cn(
          'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-default',
          active
            ? 'text-[#F8FAFC] bg-[#1E293B]'
            : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
        )}
      >
        <span>{t(item.labelKey)}</span>
        <ChevronDown className={cn('h-3 w-3 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute top-full left-0 mt-1 w-56 rounded-lg border border-[#334155] bg-[#1E293B] py-1 shadow-xl"
        >
          {item.children.map((child) => {
            const childActive = isActive(pathname, child.href);
            return (
              <Link
                key={child.href}
                href={child.href}
                role="menuitem"
                onClick={() => setOpen(false)}
                className={cn(
                  'flex items-center gap-2.5 px-4 py-2.5 text-sm transition-default',
                  childActive
                    ? 'text-[#F8FAFC] bg-[#06B6D4]/10'
                    : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#334155]',
                )}
              >
                {child.icon}
                <span>{t(child.labelKey)}</span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Mobile collapsible section ── */

function MobileSection({ item, pathname, t, onNavigate }: {
  item: NavDropdown;
  pathname: string;
  t: (key: string) => string;
  onNavigate: () => void;
}) {
  const [expanded, setExpanded] = useState(isGroupActive(pathname, item.children));

  return (
    <div>
      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className={cn(
          'flex w-full items-center justify-between rounded-md px-3 py-2.5 text-sm transition-default',
          isGroupActive(pathname, item.children)
            ? 'text-[#F8FAFC] bg-[#1E293B]'
            : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
        )}
      >
        <span className="flex items-center gap-2.5">
          {item.icon}
          <span>{t(item.labelKey)}</span>
        </span>
        <ChevronRight className={cn('h-4 w-4 transition-transform', expanded && 'rotate-90')} />
      </button>

      {expanded && (
        <div className="ml-6 mt-0.5 space-y-0.5 border-l border-[#334155] pl-3">
          {item.children.map((child) => {
            const childActive = isActive(pathname, child.href);
            return (
              <Link
                key={child.href}
                href={child.href}
                onClick={onNavigate}
                className={cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-default',
                  childActive
                    ? 'text-[#F8FAFC] bg-[#06B6D4]/10'
                    : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
                )}
              >
                {child.icon}
                <span>{t(child.labelKey)}</span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Header ── */

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
              if (isDropdown(item)) {
                return <DesktopDropdown key={item.labelKey} item={item} pathname={pathname} t={t} />;
              }
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-default',
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

            {/* Report CTA button — always visible, stands out */}
            <Link
              href="/report"
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-default ml-1',
                pathname.startsWith('/report')
                  ? 'bg-[#F59E0B] text-[#0F172A]'
                  : 'bg-[#F59E0B]/20 text-[#F59E0B] hover:bg-[#F59E0B] hover:text-[#0F172A]',
              )}
            >
              <AlertTriangle className="h-4 w-4" />
              <span>{t('report')}</span>
            </Link>
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {/* Mobile Report CTA — visible outside hamburger */}
            <Link
              href="/report"
              className="md:hidden flex items-center gap-1 rounded-md bg-[#F59E0B]/20 px-2.5 py-1.5 text-xs font-medium text-[#F59E0B] hover:bg-[#F59E0B] hover:text-[#0F172A] transition-default"
              aria-label="Report a child"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>{t('report')}</span>
            </Link>

            <LanguageToggle />

            {/* Mobile hamburger */}
            <button
              onClick={() => setIsMenuOpen((v) => !v)}
              className="md:hidden flex items-center justify-center h-11 w-11 rounded-md text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B] transition-default"
              aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={isMenuOpen}
            >
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile drawer */}
        <div
          className={cn(
            'md:hidden overflow-hidden transition-all duration-300 ease-in-out border-t border-[#334155]/50',
            isMenuOpen ? 'max-h-[500px]' : 'max-h-0 border-t-transparent',
          )}
        >
          <nav className="bg-glass px-4 py-2 space-y-0.5">
            {NAV_ITEMS.map((item) => {
              if (isDropdown(item)) {
                return (
                  <MobileSection
                    key={item.labelKey}
                    item={item}
                    pathname={pathname}
                    t={t}
                    onNavigate={() => setIsMenuOpen(false)}
                  />
                );
              }
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMenuOpen(false)}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'flex items-center gap-2.5 rounded-md px-3 py-2.5 text-sm transition-default',
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
