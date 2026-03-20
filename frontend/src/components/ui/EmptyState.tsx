'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      <div className="mb-3 text-[#94A3B8]">{icon}</div>
      <h3 className="text-sm font-semibold text-[#F8FAFC] mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-[#94A3B8] max-w-xs mb-4">{description}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="rounded-md bg-[#06B6D4] px-4 py-1.5 text-xs font-medium text-[#0F172A] hover:bg-[#06B6D4]/90 transition-default"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
