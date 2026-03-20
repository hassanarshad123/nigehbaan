'use client';

import React from 'react';
import { Download } from 'lucide-react';
import { buildExportUrl } from '@/lib/api';
import { cn } from '@/lib/utils';

interface ExportButtonProps {
  table: string;
  params?: Record<string, string>;
  label?: string;
  className?: string;
}

export function ExportButton({ table, params, label = 'Export CSV', className }: ExportButtonProps) {
  const url = buildExportUrl(table, params);

  return (
    <a
      href={url}
      download
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border border-[#334155] px-3 py-1.5 text-xs',
        'text-[#94A3B8] hover:text-[#F8FAFC] hover:border-[#06B6D4] transition-default',
        className,
      )}
    >
      <Download className="h-3.5 w-3.5" />
      {label}
    </a>
  );
}
