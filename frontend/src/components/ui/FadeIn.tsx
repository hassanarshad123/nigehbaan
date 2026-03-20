'use client';

import { cn } from '@/lib/utils';

interface FadeInProps {
  children: React.ReactNode;
  className?: string;
}

export function FadeIn({ children, className }: FadeInProps) {
  return (
    <div className={cn('animate-fade-in', className)}>
      {children}
    </div>
  );
}
