'use client';

import React from 'react';
import { useMapStore } from '@/stores/mapStore';
import type { MapLayerId } from '@/types';

interface LegendEntry {
  color: string;
  shape: 'circle' | 'line' | 'square';
  label: string;
}

const LAYER_LEGENDS: Record<MapLayerId, LegendEntry[]> = {
  incidents: [
    { color: '#EF4444', shape: 'circle', label: 'Sexual Abuse / Exploitation' },
    { color: '#DC2626', shape: 'circle', label: 'Kidnapping / Trafficking' },
    { color: '#F97316', shape: 'circle', label: 'Child / Bonded Labor' },
    { color: '#EC4899', shape: 'circle', label: 'Child Marriage' },
    { color: '#6366F1', shape: 'circle', label: 'Online Exploitation' },
    { color: '#991B1B', shape: 'circle', label: 'Child Murder' },
    { color: '#F59E0B', shape: 'circle', label: 'Missing Children' },
    { color: '#94A3B8', shape: 'circle', label: 'Other' },
  ],
  kilns: [
    { color: '#F97316', shape: 'square', label: 'Active Kiln' },
    { color: '#78716C', shape: 'square', label: 'Inactive Kiln' },
  ],
  routes: [
    { color: '#EC4899', shape: 'line', label: 'Internal Route' },
    { color: '#EF4444', shape: 'line', label: 'Cross-border Route' },
  ],
  borders: [
    { color: '#F59E0B', shape: 'circle', label: 'Formal Crossing' },
    { color: '#EF4444', shape: 'circle', label: 'Informal Crossing' },
  ],
  poverty: [
    { color: '#10B981', shape: 'square', label: 'Low Poverty (<20%)' },
    { color: '#F59E0B', shape: 'square', label: 'Moderate (20-40%)' },
    { color: '#EF4444', shape: 'square', label: 'High Poverty (>40%)' },
  ],
  flood: [
    { color: '#3B82F6', shape: 'square', label: 'Flood-affected (2022)' },
    { color: '#06B6D4', shape: 'square', label: 'Flood-prone Zone' },
  ],
};

function ShapeIcon({ shape, color }: { shape: LegendEntry['shape']; color: string }) {
  if (shape === 'circle') {
    return (
      <span
        className="inline-block h-2.5 w-2.5 rounded-full"
        style={{ backgroundColor: color }}
      />
    );
  }
  if (shape === 'line') {
    return (
      <span
        className="inline-block h-0.5 w-4 rounded-full"
        style={{ backgroundColor: color }}
      />
    );
  }
  return (
    <span
      className="inline-block h-2.5 w-2.5 rounded-sm"
      style={{ backgroundColor: color }}
    />
  );
}

export function MapLegend() {
  const activeLayers = useMapStore((s) => s.activeLayers);

  const entries = activeLayers.flatMap(
    (layerId) => LAYER_LEGENDS[layerId] ?? [],
  );

  if (entries.length === 0) return null;

  return (
    <div className="rounded-lg border border-[#334155] bg-glass-surface p-3 w-full sm:w-56">
      <p className="text-xs font-medium uppercase tracking-wider text-[#94A3B8] mb-2">
        Legend
      </p>
      <div className="space-y-1.5">
        {entries.map((entry, idx) => (
          <div key={`${entry.label}-${idx}`} className="flex items-center gap-2 text-xs text-[#F8FAFC]">
            <ShapeIcon shape={entry.shape} color={entry.color} />
            <span>{entry.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
