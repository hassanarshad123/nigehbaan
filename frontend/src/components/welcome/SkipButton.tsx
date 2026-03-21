'use client';

import React from 'react';

interface SkipButtonProps {
  onClick: () => void;
  label?: string;
}

export function SkipButton({ onClick, label = 'Skip' }: SkipButtonProps) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-[110] min-h-[44px] min-w-[44px] px-4 py-2 text-sm text-[#94A3B8] hover:text-[#F8FAFC] transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#06B6D4] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0F172A] rounded-lg"
      aria-label={label}
    >
      {label}
    </button>
  );
}
