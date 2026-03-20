'use client';

import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface QueryErrorFallbackProps {
  message?: string;
  onRetry?: () => void;
}

export function QueryErrorFallback({
  message = 'Failed to load data. Please try again.',
  onRetry,
}: QueryErrorFallbackProps) {
  return (
    <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 px-4 py-6 text-center">
      <AlertTriangle className="mx-auto h-6 w-6 text-[#EF4444] mb-2" />
      <p className="text-sm text-[#EF4444] mb-3">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 rounded-md border border-[#EF4444]/30 px-3 py-1.5 text-xs text-[#EF4444] hover:bg-[#EF4444]/10 transition-default"
        >
          <RotateCcw className="h-3 w-3" />
          Retry
        </button>
      )}
    </div>
  );
}
