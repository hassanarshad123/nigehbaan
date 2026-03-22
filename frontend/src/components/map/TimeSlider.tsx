'use client';

import React, { useCallback } from 'react';
import { useMapStore } from '@/stores/mapStore';
import { Calendar } from 'lucide-react';

const MIN_YEAR = 2010;
const MAX_YEAR = 2024;

export function TimeSlider() {
  const yearRange = useMapStore((s) => s.yearRange);
  const setYearRange = useMapStore((s) => s.setYearRange);

  const handleMinChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = Number(e.target.value);
      if (val <= yearRange[1]) {
        setYearRange([val, yearRange[1]]);
      }
    },
    [yearRange, setYearRange],
  );

  const handleMaxChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = Number(e.target.value);
      if (val >= yearRange[0]) {
        setYearRange([yearRange[0], val]);
      }
    },
    [yearRange, setYearRange],
  );

  return (
    <div className="rounded-lg border border-[#334155]/60 bg-[#1E293B]/80 backdrop-blur-md px-4 py-3 w-full max-w-sm mx-auto" data-tour-step="timeline">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5 text-[#06B6D4]" />
          <span className="text-xs font-medium text-[#94A3B8]">Year Range</span>
        </div>
        <span className="text-xs font-mono text-[#F8FAFC] tabular-nums">
          {yearRange[0]} &ndash; {yearRange[1]}
        </span>
      </div>

      <div className="relative h-6">
        {/* Track background */}
        <div className="absolute top-1/2 left-0 right-0 h-1 -translate-y-1/2 rounded-full bg-[#334155]" />
        {/* Active range highlight */}
        <div
          className="absolute top-1/2 h-1 -translate-y-1/2 rounded-full bg-[#06B6D4]/60"
          style={{
            left: `${((yearRange[0] - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100}%`,
            right: `${100 - ((yearRange[1] - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100}%`,
          }}
        />
        {/* Min handle */}
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={yearRange[0]}
          onChange={handleMinChange}
          className="absolute inset-0 w-full appearance-none bg-transparent pointer-events-auto cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#06B6D4] [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[#0F172A] [&::-webkit-slider-thumb]:shadow-md"
          style={{ zIndex: yearRange[0] === yearRange[1] ? 5 : 3 }}
        />
        {/* Max handle */}
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={yearRange[1]}
          onChange={handleMaxChange}
          className="absolute inset-0 w-full appearance-none bg-transparent pointer-events-auto cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#06B6D4] [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[#0F172A] [&::-webkit-slider-thumb]:shadow-md"
          style={{ zIndex: 4 }}
        />
      </div>

      <div className="flex justify-between text-xs text-[#64748B] mt-1 tabular-nums">
        <span>{MIN_YEAR}</span>
        <span>{MAX_YEAR}</span>
      </div>
    </div>
  );
}
