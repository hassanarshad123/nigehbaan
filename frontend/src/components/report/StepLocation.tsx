'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { MapPin, Pencil } from 'lucide-react';
import type { ReportFormData } from './ReportForm';

interface StepLocationProps {
  data: ReportFormData;
  onChange: (partial: Partial<ReportFormData>) => void;
}

export function StepLocation({ data, onChange }: StepLocationProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[#F8FAFC] mb-1">
        Where did you observe this?
      </h2>
      <p className="text-sm text-[#94A3B8] mb-6">
        Enter an address or description of the location.
      </p>

      {/* Address input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-[#94A3B8] mb-1.5">
          <Pencil className="inline h-3.5 w-3.5 mr-1" />
          Address or Landmark
        </label>
        <input
          type="text"
          value={data.address}
          onChange={(e) => onChange({ address: e.target.value })}
          placeholder="e.g. Near Data Darbar, Lahore"
          className={cn(
            'w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2.5 text-sm text-[#F8FAFC]',
            'placeholder-[#94A3B8] outline-none border-glow-focus transition-default',
          )}
        />
      </div>

      {/* Map pin placeholder */}
      <div className="rounded-lg border border-dashed border-[#334155] bg-[#0F172A] p-8 text-center">
        <MapPin className="mx-auto h-8 w-8 text-[#94A3B8] mb-2" />
        <p className="text-sm text-[#94A3B8] mb-1">Or pin the location on the map</p>
        <p className="text-xs text-[#334155]">
          Interactive map picker will be available when Mapbox token is configured
        </p>

        {data.latitude !== null && data.longitude !== null && (
          <div className="mt-3 text-xs text-[#06B6D4]">
            Selected: {data.latitude.toFixed(4)}, {data.longitude.toFixed(4)}
          </div>
        )}
      </div>
    </div>
  );
}
