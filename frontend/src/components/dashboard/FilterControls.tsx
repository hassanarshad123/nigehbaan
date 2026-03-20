'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { useFilterStore } from '@/stores/filterStore';
import type { IncidentType } from '@/types';
import { Filter, RotateCcw } from 'lucide-react';

const PROVINCES = [
  'Punjab',
  'Sindh',
  'Khyber Pakhtunkhwa',
  'Balochistan',
  'Islamabad',
  'AJK',
  'Gilgit-Baltistan',
];

const INCIDENT_TYPE_GROUPS: { category: string; types: { value: IncidentType; label: string }[] }[] = [
  {
    category: 'Violence & Abuse',
    types: [
      { value: 'sexual_abuse', label: 'Sexual Abuse' },
      { value: 'physical_abuse', label: 'Physical Abuse' },
      { value: 'child_murder', label: 'Child Murder' },
      { value: 'honor_killing', label: 'Honor Killing' },
    ],
  },
  {
    category: 'Trafficking & Exploitation',
    types: [
      { value: 'kidnapping', label: 'Kidnapping' },
      { value: 'child_trafficking', label: 'Child Trafficking' },
      { value: 'sexual_exploitation', label: 'Sexual Exploitation' },
      { value: 'online_exploitation', label: 'Online Exploitation' },
      { value: 'child_pornography', label: 'Child Pornography' },
    ],
  },
  {
    category: 'Labor & Marriage',
    types: [
      { value: 'child_labor', label: 'Child Labor' },
      { value: 'bonded_labor', label: 'Bonded Labor' },
      { value: 'child_marriage', label: 'Child Marriage' },
      { value: 'begging_ring', label: 'Begging Ring' },
    ],
  },
  {
    category: 'Other',
    types: [
      { value: 'missing', label: 'Missing' },
      { value: 'organ_trafficking', label: 'Organ Trafficking' },
      { value: 'abandonment', label: 'Abandonment' },
      { value: 'medical_negligence', label: 'Medical Negligence' },
      { value: 'other', label: 'Other' },
    ],
  },
];

export function FilterControls() {
  const {
    selectedProvince,
    yearRange,
    selectedTypes,
    setSelectedProvince,
    setYearRange,
    toggleType,
    resetFilters,
  } = useFilterStore();

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#F8FAFC]">
          <Filter className="h-4 w-4 text-[#06B6D4]" />
          Filters
        </div>
        <button
          onClick={resetFilters}
          className="flex items-center gap-1 text-xs text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
        >
          <RotateCcw className="h-3 w-3" />
          Reset
        </button>
      </div>

      <div className="flex flex-wrap gap-4">
        {/* Province selector */}
        <div className="min-w-[160px]">
          <label className="block text-xs text-[#94A3B8] mb-1">Province</label>
          <select
            value={selectedProvince ?? ''}
            onChange={(e) =>
              setSelectedProvince(e.target.value || null)
            }
            className={cn(
              'w-full rounded-md border border-[#334155] bg-[#0F172A] px-2.5 py-1.5 text-sm text-[#F8FAFC]',
              'outline-none border-glow-focus transition-default',
            )}
          >
            <option value="">All Provinces</option>
            {PROVINCES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        {/* Year range */}
        <div className="min-w-[200px]">
          <label className="block text-xs text-[#94A3B8] mb-1">
            Year Range: {yearRange[0]} - {yearRange[1]}
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={2010}
              max={yearRange[1]}
              value={yearRange[0]}
              onChange={(e) =>
                setYearRange([Number(e.target.value), yearRange[1]])
              }
              className={cn(
                'w-20 rounded-md border border-[#334155] bg-[#0F172A] px-2 py-1.5 text-sm text-[#F8FAFC]',
                'outline-none border-glow-focus transition-default',
              )}
            />
            <span className="text-[#94A3B8]">-</span>
            <input
              type="number"
              min={yearRange[0]}
              max={2024}
              value={yearRange[1]}
              onChange={(e) =>
                setYearRange([yearRange[0], Number(e.target.value)])
              }
              className={cn(
                'w-20 rounded-md border border-[#334155] bg-[#0F172A] px-2 py-1.5 text-sm text-[#F8FAFC]',
                'outline-none border-glow-focus transition-default',
              )}
            />
          </div>
        </div>

        {/* Incident type multi-select grouped by category */}
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs text-[#94A3B8] mb-1">Incident Type</label>
          <div className="space-y-2">
            {INCIDENT_TYPE_GROUPS.map((group) => (
              <div key={group.category}>
                <span className="text-[10px] uppercase tracking-wider text-[#64748B] mb-0.5 block">
                  {group.category}
                </span>
                <div className="flex flex-wrap gap-1">
                  {group.types.map((type) => {
                    const isSelected = selectedTypes.includes(type.value);
                    return (
                      <button
                        key={type.value}
                        onClick={() => toggleType(type.value)}
                        className={cn(
                          'rounded-md px-2 py-1 text-xs transition-default',
                          isSelected
                            ? 'bg-[#06B6D4]/20 text-[#06B6D4] border border-[#06B6D4]/40'
                            : 'bg-[#0F172A] text-[#94A3B8] border border-[#334155] hover:border-[#94A3B8]',
                        )}
                      >
                        {type.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
