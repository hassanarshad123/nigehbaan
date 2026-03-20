'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { LanguageToggle } from './LanguageToggle';
import { Map, BarChart3, FileWarning, Scale, LifeBuoy, Info } from 'lucide-react';

interface NavItem {
  href: string;
  label: string;
  labelUr: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/', label: 'Map', labelUr: 'نقشہ', icon: <Map className="h-4 w-4" /> },
  { href: '/dashboard', label: 'Dashboard', labelUr: 'ڈیش بورڈ', icon: <BarChart3 className="h-4 w-4" /> },
  { href: '/report', label: 'Report', labelUr: 'رپورٹ', icon: <FileWarning className="h-4 w-4" /> },
  { href: '/legal', label: 'Legal', labelUr: 'قانونی', icon: <Scale className="h-4 w-4" /> },
  { href: '/resources', label: 'Resources', labelUr: 'وسائل', icon: <LifeBuoy className="h-4 w-4" /> },
  { href: '/about', label: 'About', labelUr: 'تعارف', icon: <Info className="h-4 w-4" /> },
];

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-glass border-b border-[#334155]/50">
      <div className="mx-auto flex h-12 max-w-screen-2xl items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="font-urdu text-lg text-[#06B6D4]">نگہبان</span>
          <span className="text-sm font-semibold tracking-wide text-[#F8FAFC]">
            Nigehbaan
          </span>
        </Link>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm',
                'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
                'transition-default',
              )}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <LanguageToggle />
        </div>
      </div>
    </header>
  );
}
