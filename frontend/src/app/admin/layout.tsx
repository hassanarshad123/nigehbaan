'use client';

import React, { type ReactNode } from 'react';
import { useSession } from 'next-auth/react';
import { Header } from '@/components/layout/Header';
import { LoginForm } from '@/components/admin/LoginForm';
import { Loader2 } from 'lucide-react';

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
      <div className="pt-12">{children}</div>
    </div>
  );
}
