'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Layers, X } from 'lucide-react';
import { LayerControls } from './LayerControls';
import { MapLegend } from './MapLegend';

export function MobileMapControls() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Desktop: always show both components */}
      <div className="hidden sm:block space-y-2">
        <LayerControls />
        <MapLegend />
      </div>

      {/* Mobile: toggle button + panel */}
      <div className="sm:hidden relative">
        <button
          onClick={() => setIsOpen((v) => !v)}
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-lg border border-[#334155] bg-glass-surface transition-default',
            isOpen ? 'text-[#06B6D4]' : 'text-[#94A3B8] hover:text-[#F8FAFC]',
          )}
          aria-label={isOpen ? 'Close layer controls' : 'Open layer controls'}
        >
          {isOpen ? <X className="h-5 w-5" /> : <Layers className="h-5 w-5" />}
        </button>

        {isOpen && (
          <div className="absolute top-12 right-0 w-56 space-y-2 z-50">
            <LayerControls />
            <MapLegend />
          </div>
        )}
      </div>
    </>
  );
}
