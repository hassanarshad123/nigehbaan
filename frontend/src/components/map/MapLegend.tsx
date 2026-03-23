'use client';

import React from 'react';
import { useMapStore } from '@/stores/mapStore';
import { useMapData } from '@/hooks/useMapData';
import { INCIDENT_TYPE_COLORS, INCIDENT_TYPE_LABELS } from '@/lib/incidentColors';
import type { IncidentType, MapLayerId } from '@/types';

interface LegendEntry {
  color: string;
  shape: 'circle' | 'line' | 'square';
  label: string;
}

const STATIC_LEGENDS: Partial<Record<MapLayerId, LegendEntry[]>> = {
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
    { color: '#10B981', shape: 'square', label: 'Low Risk' },
    { color: '#FBBF24', shape: 'square', label: 'Moderate Risk' },
    { color: '#EF4444', shape: 'square', label: 'High Risk' },
  ],
  missing: [
    { color: '#3B82F6', shape: 'circle', label: 'Missing Child' },
  ],
  reports: [
    { color: '#FBBF24', shape: 'circle', label: 'Public Report' },
  ],
  convictions: [
    { color: '#EF4444', shape: 'square', label: '0% Conviction' },
    { color: '#FBBF24', shape: 'square', label: '50% Conviction' },
    { color: '#10B981', shape: 'square', label: '70%+ Conviction' },
  ],
};

function ShapeIcon({ shape, color }: { shape: LegendEntry['shape']; color: string }) {
  if (shape === 'circle') {
    return (
      <span
        className="inline-block h-2.5 w-2.5 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
    );
  }
  if (shape === 'line') {
    return (
      <span
        className="inline-block h-0.5 w-4 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
    );
  }
  return (
    <span
      className="inline-block h-2.5 w-2.5 rounded-sm shrink-0"
      style={{ backgroundColor: color }}
    />
  );
}

export function MapLegend() {
  const activeLayers = useMapStore((s) => s.activeLayers);
  const { filteredIncidents } = useMapData();

  // Compute type counts from actual incident data
  const typeCounts = React.useMemo(() => {
    const counts: Record<string, number> = {};
    for (const f of filteredIncidents?.features ?? []) {
      const t = String(f.properties?.incidentType ?? 'other');
      counts[t] = (counts[t] ?? 0) + 1;
    }
    return counts;
  }, [filteredIncidents]);

  // Build incident legend entries dynamically (only types with count > 0)
  const incidentEntries: (LegendEntry & { count: number })[] = React.useMemo(() => {
    const entries: (LegendEntry & { count: number })[] = [];
    for (const [type, color] of Object.entries(INCIDENT_TYPE_COLORS)) {
      const count = typeCounts[type] ?? 0;
      if (count > 0) {
        entries.push({
          color,
          shape: 'circle',
          label: INCIDENT_TYPE_LABELS[type as IncidentType] ?? type,
          count,
        });
      }
    }
    return entries.sort((a, b) => b.count - a.count);
  }, [typeCounts]);

  // Static legend entries for non-incident layers
  const staticEntries = activeLayers
    .filter((id) => id !== 'incidents')
    .flatMap((layerId) => STATIC_LEGENDS[layerId] ?? []);

  const showIncidents = activeLayers.includes('incidents');
  const hasEntries = (showIncidents && incidentEntries.length > 0) || staticEntries.length > 0;

  if (!hasEntries) return null;

  return (
    <div className="rounded-lg border border-[#334155] bg-glass-surface p-3 w-full sm:w-56 max-h-80 overflow-y-auto">
      <p className="text-xs font-medium uppercase tracking-wider text-[#94A3B8] mb-2">
        Legend
      </p>

      {/* Dynamic incident type legend */}
      {showIncidents && incidentEntries.length > 0 && (
        <div className="mb-2">
          <div className="space-y-1">
            {incidentEntries.map((entry) => (
              <div key={entry.label} className="flex items-center gap-2 text-xs text-[#F8FAFC]">
                <ShapeIcon shape={entry.shape} color={entry.color} />
                <span className="flex-1 truncate">{entry.label}</span>
                <span className="text-[#94A3B8] text-xs tabular-nums">{entry.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Divider between incident and static legends */}
      {showIncidents && incidentEntries.length > 0 && staticEntries.length > 0 && (
        <div className="border-t border-[#334155] my-2" />
      )}

      {/* Static layer legends */}
      {staticEntries.length > 0 && (
        <div className="space-y-1.5">
          {staticEntries.map((entry, idx) => (
            <div key={`${entry.label}-${idx}`} className="flex items-center gap-2 text-xs text-[#F8FAFC]">
              <ShapeIcon shape={entry.shape} color={entry.color} />
              <span>{entry.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
