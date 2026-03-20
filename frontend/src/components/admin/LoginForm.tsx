'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signIn } from 'next-auth/react';
import { ShieldCheck, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const result = await signIn('credentials', {
      email,
      password,
      redirect: false,
    });

    if (result?.error) {
      setError('Invalid email or password');
      setLoading(false);
    } else {
      router.refresh();
    }
  };

  return (
    <div className="mx-auto max-w-sm">
      <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6">
        <div className="flex items-center gap-2 mb-6 justify-center">
          <ShieldCheck className="h-6 w-6 text-[#06B6D4]" />
          <h2 className="text-lg font-semibold text-[#F8FAFC]">Admin Login</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-[#94A3B8] mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@nigehbaan.org"
              required
              className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2 text-sm text-[#F8FAFC] outline-none focus:border-[#06B6D4] transition-default"
            />
          </div>

          <div>
            <label className="block text-xs text-[#94A3B8] mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              className="w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2 text-sm text-[#F8FAFC] outline-none focus:border-[#06B6D4] transition-default"
            />
          </div>

          {error && (
            <p className="text-xs text-[#EF4444]">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className={cn(
              'w-full rounded-md px-4 py-2 text-sm font-medium transition-default',
              'bg-[#06B6D4] text-[#0F172A] hover:bg-[#06B6D4]/90',
              loading && 'opacity-60 cursor-not-allowed',
            )}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
