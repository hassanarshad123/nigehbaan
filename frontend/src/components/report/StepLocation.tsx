'use client';

import React, { useCallback } from 'react';
import dynamic from 'next/dynamic';
import { cn } from '@/lib/utils';
import { MapPin, Pencil, Loader2 } from 'lucide-react';
import type { ReportFormData } from './ReportForm';

const LocationPicker = dynamic(
  () => import('./LocationPicker').then((m) => m.LocationPicker),
  {
    ssr: false,
    loading: () => (
      <div className="rounded-lg border border-dashed border-[#334155] bg-[#0F172A] h-64 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
      </div>
    ),
  },
);

interface StepLocationProps {
  data: ReportFormData;
  onChange: (partial: Partial<ReportFormData>) => void;
}

export function StepLocation({ data, onChange }: StepLocationProps) {
  const handleMapClick = useCallback(
    (lat: number, lon: number) => {
      onChange({ latitude: lat, longitude: lon });
    },
    [onChange],
  );

  return (
    <div>
      <h2 className="text-lg font-semibold text-[#F8FAFC] mb-1">
        Where did you observe this?
      </h2>
      <p className="text-sm text-[#94A3B8] mb-6">
        Enter an address or pin the location on the map.
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

      {/* Map picker */}
      <LocationPicker
        latitude={data.latitude}
        longitude={data.longitude}
        onClick={handleMapClick}
      />

      {data.latitude !== null && data.longitude !== null && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-[#06B6D4]">
          <MapPin className="h-3 w-3" />
          Selected: {data.latitude.toFixed(4)}, {data.longitude.toFixed(4)}
        </div>
      )}
    </div>
  );
}
