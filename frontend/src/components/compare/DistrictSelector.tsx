'use client';

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchDistrictList, type DistrictListItem } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Search, X, MapPin } from 'lucide-react';

interface DistrictSelectorProps {
  selected: string[];
  onChange: (pcodes: string[]) => void;
  max?: number;
}

export function DistrictSelector({ selected, onChange, max = 4 }: DistrictSelectorProps) {
  const { data: districts } = useQuery({
    queryKey: ['district-list'],
    queryFn: fetchDistrictList,
    staleTime: 5 * 60_000,
  });

  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const districtMap = useMemo(() => {
    const map = new Map<string, DistrictListItem>();
    for (const d of districts ?? []) {
      map.set(d.pcode, d);
    }
    return map;
  }, [districts]);

  const filtered = useMemo(() => {
    if (!districts) return [];
    const q = query.toLowerCase();
    return districts
      .filter((d) => !selected.includes(d.pcode))
      .filter((d) =>
        d.nameEn.toLowerCase().includes(q) ||
        d.province.toLowerCase().includes(q) ||
        d.pcode.toLowerCase().includes(q),
      )
      .slice(0, 20);
  }, [districts, query, selected]);

  const addDistrict = (pcode: string) => {
    if (selected.length < max && !selected.includes(pcode)) {
      onChange([...selected, pcode]);
    }
    setQuery('');
    setIsOpen(false);
  };

  const removeDistrict = (pcode: string) => {
    onChange(selected.filter((p) => p !== pcode));
  };

  return (
    <div ref={wrapperRef} className="relative">
      {/* Selected tags */}
      <div className="flex flex-wrap gap-2 mb-3">
        {selected.map((pcode) => {
          const d = districtMap.get(pcode);
          return (
            <span
              key={pcode}
              className="inline-flex items-center gap-1.5 rounded-full bg-[#06B6D4]/10 border border-[#06B6D4]/30 px-3 py-1 text-xs text-[#06B6D4]"
            >
              <MapPin className="h-3 w-3" />
              {d?.nameEn ?? pcode}
              <button
                onClick={() => removeDistrict(pcode)}
                className="hover:text-[#F8FAFC] transition-default"
                aria-label={`Remove ${d?.nameEn ?? pcode}`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          );
        })}
      </div>

      {/* Search input */}
      {selected.length < max && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#94A3B8]" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            placeholder={`Add district (${selected.length}/${max})...`}
            className={cn(
              'w-full rounded-md border border-[#334155] bg-[#0F172A] pl-9 pr-3 py-2 text-sm text-[#F8FAFC]',
              'placeholder-[#94A3B8] outline-none border-glow-focus transition-default',
            )}
          />

          {/* Dropdown */}
          {isOpen && filtered.length > 0 && (
            <div className="absolute top-full left-0 right-0 z-50 mt-1 max-h-48 overflow-auto rounded-md border border-[#334155] bg-[#1E293B] shadow-xl">
              {filtered.map((d) => (
                <button
                  key={d.pcode}
                  onClick={() => addDistrict(d.pcode)}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm text-[#F8FAFC] hover:bg-[#334155] transition-default text-left"
                >
                  <span>{d.nameEn}</span>
                  <span className="text-xs text-[#94A3B8]">{d.province}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
