'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { useFilterStore } from '@/stores/filterStore';
import { useMapStore } from '@/stores/mapStore';
import { useMapData } from '@/hooks/useMapData';
import { INCIDENT_TYPE_COLORS, INCIDENT_TYPE_LABELS } from '@/lib/incidentColors';
import type { IncidentType } from '@/types';
import { Filter, ChevronUp } from 'lucide-react';

const ALL_TYPES = Object.keys(INCIDENT_TYPE_COLORS) as IncidentType[];

export function FilterDrawer() {
  const selectedTypes = useFilterStore((s) => s.selectedTypes);
  const toggleType = useFilterStore((s) => s.toggleType);
  const setSelectedTypes = useFilterStore((s) => s.setSelectedTypes);
  const activeLayers = useMapStore((s) => s.activeLayers);
  const incidentsActive = activeLayers.includes('incidents');
  const { filteredIncidents } = useMapData();

  const [isOpen, setIsOpen] = useState(false);

  // Compute counts per type from actual data
  const typeCounts = React.useMemo(() => {
    const counts: Record<string, number> = {};
    for (const f of filteredIncidents?.features ?? []) {
      const t = String(f.properties?.incidentType ?? 'other');
      counts[t] = (counts[t] ?? 0) + 1;
    }
    return counts;
  }, [filteredIncidents]);

  const activeCount = selectedTypes.length === 0 ? ALL_TYPES.length : selectedTypes.length;

  const handleSelectAll = () => setSelectedTypes([]);
  const handleClearAll = () => setSelectedTypes(['__none__' as IncidentType]); // force empty filter

  if (!incidentsActive) return null;

  return (
    <>
      {/* Mobile FAB trigger */}
      <button
        onClick={() => setIsOpen((v) => !v)}
        className={cn(
          'sm:hidden fixed bottom-20 right-4 z-40',
          'flex items-center justify-center h-12 w-12 rounded-full shadow-lg',
          'bg-[#1E293B] border border-[#334155] text-[#06B6D4]',
          'hover:bg-[#334155] transition-default',
        )}
        aria-label="Filter incidents"
      >
        <Filter className="h-5 w-5" />
      </button>

      {/* Drawer — bottom sheet on mobile, panel on desktop */}
      <div
        className={cn(
          // Mobile: fixed bottom sheet
          'sm:relative sm:inset-auto',
          'fixed inset-x-0 bottom-0 z-50',
          'bg-[#1E293B] border-t sm:border border-[#334155] rounded-t-xl sm:rounded-lg',
          'transform transition-transform duration-300 ease-out',
          // Mobile slide
          isOpen ? 'translate-y-0' : 'translate-y-[calc(100%-0px)] sm:translate-y-0',
          // Desktop: always visible
          'sm:transform-none',
          // Width
          'sm:w-56',
        )}
      >
        {/* Drag handle — mobile only */}
        <button
          onClick={() => setIsOpen((v) => !v)}
          className="sm:hidden flex justify-center w-full py-2"
          aria-label="Toggle filter drawer"
        >
          <div className="h-1 w-10 rounded-full bg-[#334155]" />
        </button>

        <div className="px-3 pb-3 sm:py-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Filter className="h-3.5 w-3.5 text-[#06B6D4]" />
              <span className="text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
                Filter by Type
              </span>
            </div>
            <ChevronUp
              className={cn(
                'h-4 w-4 text-[#94A3B8] transition-transform sm:hidden',
                isOpen ? 'rotate-180' : '',
              )}
            />
          </div>

          {/* Select All / Clear All */}
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={handleSelectAll}
              className="text-xs text-[#06B6D4] hover:text-[#F8FAFC] transition-default"
            >
              All
            </button>
            <span className="text-[#334155]">|</span>
            <button
              onClick={handleClearAll}
              className="text-xs text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
            >
              None
            </button>
            <span className="ml-auto text-xs text-[#94A3B8]">
              {activeCount}/{ALL_TYPES.length}
            </span>
          </div>

          {/* Type chips grid */}
          <div className="grid grid-cols-2 gap-1 max-h-60 overflow-y-auto">
            {ALL_TYPES.map((type) => {
              const color = INCIDENT_TYPE_COLORS[type];
              const label = INCIDENT_TYPE_LABELS[type];
              const count = typeCounts[type] ?? 0;
              const isActive = selectedTypes.length === 0 || selectedTypes.includes(type);

              return (
                <button
                  key={type}
                  onClick={() => toggleType(type)}
                  className={cn(
                    'flex items-center gap-1.5 rounded px-2 py-1 text-xs transition-default text-left',
                    isActive
                      ? 'bg-[#0F172A] text-[#F8FAFC]'
                      : 'bg-transparent text-[#94A3B8]/50',
                  )}
                >
                  <span
                    className={cn(
                      'inline-block h-2 w-2 rounded-full shrink-0 transition-opacity',
                      isActive ? 'opacity-100' : 'opacity-30',
                    )}
                    style={{ backgroundColor: color }}
                  />
                  <span className="truncate flex-1">{label}</span>
                  {count > 0 && (
                    <span className="text-[#94A3B8] text-xs tabular-nums">{count}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Backdrop — mobile only */}
      {isOpen && (
        <div
          className="sm:hidden fixed inset-0 z-[45] bg-black/30"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
