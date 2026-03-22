'use client';

import React, { useCallback } from 'react';
import { useMapStore } from '@/stores/mapStore';
import { Calendar } from 'lucide-react';

const MIN_YEAR = 2010;
const MAX_YEAR = 2024;

export function IncidentTimeline() {
  const yearRange = useMapStore((s) => s.yearRange);
  const setYearRange = useMapStore((s) => s.setYearRange);

  const handleStartChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const start = Math.min(Number(e.target.value), yearRange[1]);
      setYearRange([start, yearRange[1]]);
    },
    [yearRange, setYearRange],
  );

  const handleEndChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const end = Math.max(Number(e.target.value), yearRange[0]);
      setYearRange([yearRange[0], end]);
    },
    [yearRange, setYearRange],
  );

  const pctStart = ((yearRange[0] - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100;
  const pctEnd = ((yearRange[1] - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100;

  return (
    <div className="rounded-lg border border-[#334155] bg-glass-surface p-3 w-full sm:w-72">
      <div className="flex items-center gap-2 mb-3 text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
        <Calendar className="h-3.5 w-3.5" />
        <span>Timeline</span>
      </div>

      {/* Year labels */}
      <div className="flex justify-between text-sm font-medium text-[#F8FAFC] mb-2">
        <span>{yearRange[0]}</span>
        <span>{yearRange[1]}</span>
      </div>

      {/* Range track */}
      <div className="relative h-2 rounded-full bg-[#334155] mb-2">
        <div
          className="absolute h-2 rounded-full bg-[#06B6D4]"
          style={{
            left: `${pctStart}%`,
            width: `${pctEnd - pctStart}%`,
          }}
        />
      </div>

      {/* Range inputs (overlapping for dual-thumb effect) */}
      <div className="relative h-5">
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={yearRange[0]}
          onChange={handleStartChange}
          className="absolute inset-0 w-full appearance-none bg-transparent pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#06B6D4] [&::-webkit-slider-thumb]:cursor-pointer"
          aria-label="Start year"
        />
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={yearRange[1]}
          onChange={handleEndChange}
          className="absolute inset-0 w-full appearance-none bg-transparent pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#06B6D4] [&::-webkit-slider-thumb]:cursor-pointer"
          aria-label="End year"
        />
      </div>

      {/* Tick marks */}
      <div className="flex justify-between text-xs text-[#94A3B8] mt-1">
        {Array.from({ length: 8 }, (_, i) => MIN_YEAR + i * 2).map((year) => (
          <span key={year}>{year}</span>
        ))}
      </div>
    </div>
  );
}
