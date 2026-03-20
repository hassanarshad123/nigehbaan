'use client';

import React, { type ReactNode } from 'react';
import { Header } from '@/components/layout/Header';
import { ShieldAlert } from 'lucide-react';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  // Auth check placeholder — in production this would use next-auth session
  const isAuthenticated = true; // Placeholder

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#0F172A]">
        <Header />
        <main className="flex items-center justify-center pt-32">
          <div className="rounded-lg border border-[#EF4444]/30 bg-[#1E293B] p-8 text-center max-w-md">
            <ShieldAlert className="mx-auto h-10 w-10 text-[#EF4444] mb-3" />
            <h1 className="text-lg font-semibold text-[#F8FAFC] mb-2">
              Authentication Required
            </h1>
            <p className="text-sm text-[#94A3B8]">
              You must be signed in as an administrator to access this area.
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />
      <div className="pt-12">{children}</div>
    </div>
  );
}
