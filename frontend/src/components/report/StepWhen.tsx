'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Calendar } from 'lucide-react';

interface StepWhenProps {
  date: string;
  onChange: (date: string) => void;
}

export function StepWhen({ date, onChange }: StepWhenProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[#F8FAFC] mb-1">
        When did this happen?
      </h2>
      <p className="text-sm text-[#94A3B8] mb-6">
        Provide the date or approximate time of the incident.
      </p>

      <div className="max-w-xs">
        <label className="block text-sm font-medium text-[#94A3B8] mb-1.5">
          <Calendar className="inline h-3.5 w-3.5 mr-1" />
          Date of Incident
        </label>
        <input
          type="date"
          value={date}
          onChange={(e) => onChange(e.target.value)}
          max={new Date().toISOString().split('T')[0]}
          className={cn(
            'w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2.5 text-sm text-[#F8FAFC]',
            'outline-none border-glow-focus transition-default',
            '[color-scheme:dark]',
          )}
        />
      </div>

      {/* Quick select buttons */}
      <div className="mt-4 flex flex-wrap gap-2">
        {['Today', 'Yesterday', 'This week', 'This month'].map((label) => (
          <button
            key={label}
            onClick={() => {
              const now = new Date();
              let d = new Date();
              if (label === 'Yesterday') d.setDate(now.getDate() - 1);
              if (label === 'This week') d.setDate(now.getDate() - 3);
              if (label === 'This month') d.setDate(now.getDate() - 15);
              onChange(d.toISOString().split('T')[0]);
            }}
            className={cn(
              'rounded-md border border-[#334155] bg-[#0F172A] px-3 py-1.5 text-xs text-[#94A3B8]',
              'hover:border-[#06B6D4] hover:text-[#F8FAFC] transition-default',
            )}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
