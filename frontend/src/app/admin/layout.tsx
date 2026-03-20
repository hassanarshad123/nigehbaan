'use client';

import React, { type ReactNode } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { Header } from '@/components/layout/Header';
import { LoginForm } from '@/components/admin/LoginForm';
import { Loader2, LogOut } from 'lucide-react';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-[#0F172A]">
        <Header />
        <main className="flex items-center justify-center pt-32">
          <Loader2 className="h-8 w-8 animate-spin text-[#06B6D4]" />
        </main>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-[#0F172A]">
        <Header />
        <main className="pt-32 px-4">
          <LoginForm />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />
      {/* Admin top bar */}
      <div className="fixed top-12 left-0 right-0 z-40 bg-[#1E293B] border-b border-[#334155]/50">
        <div className="mx-auto max-w-screen-2xl flex items-center justify-between px-4 h-10">
          <span className="text-xs text-[#94A3B8] truncate">
            {session.user?.email}
          </span>
          <button
            onClick={() => signOut()}
            className="flex items-center gap-1.5 rounded-md px-3 py-1 text-xs text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#334155] transition-default"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign Out
          </button>
        </div>
      </div>
      <div className="pt-[5.5rem]">{children}</div>
    </div>
  );
}
