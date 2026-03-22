'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Search, X, MapPin, Newspaper, Scale } from 'lucide-react';
import { fetchDistrictList, globalSearch, type DistrictListItem } from '@/lib/api';

interface SearchResultItem {
  pcode: string;
  name: string;
  type: 'district' | 'incident' | 'article' | 'judgment';
  snippet?: string | null;
}

interface SearchBarProps {
  onSelect?: (result: SearchResultItem) => void;
}

const TYPE_CONFIG: Record<string, { bg: string; icon: React.ReactNode }> = {
  district: { bg: 'bg-[#10B981]/10 text-[#10B981]', icon: <MapPin className="h-3 w-3" /> },
  incident: { bg: 'bg-[#EF4444]/10 text-[#EF4444]', icon: <MapPin className="h-3 w-3" /> },
  article: { bg: 'bg-[#06B6D4]/10 text-[#06B6D4]', icon: <Newspaper className="h-3 w-3" /> },
  judgment: { bg: 'bg-[#F59E0B]/10 text-[#F59E0B]', icon: <Scale className="h-3 w-3" /> },
};

export function SearchBar({ onSelect }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [districts, setDistricts] = useState<DistrictListItem[]>([]);
  const [backendResults, setBackendResults] = useState<SearchResultItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchDistrictList()
      .then(setDistricts)
      .catch(() => setDistricts([]));
  }, []);

  // Debounced backend search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (query.length < 3) {
      setBackendResults([]);
      return;
    }

    debounceRef.current = setTimeout(() => {
      const VALID_TYPES = new Set<SearchResultItem['type']>(['district', 'incident', 'article', 'judgment']);
      globalSearch(query)
        .then((results) => {
          setBackendResults(
            results.map((r) => ({
              pcode: r.districtPcode ?? '',
              name: r.title,
              type: VALID_TYPES.has(r.type as SearchResultItem['type'])
                ? (r.type as SearchResultItem['type'])
                : 'district',
              snippet: r.snippet,
            })),
          );
        })
        .catch(() => setBackendResults([]));
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  // Local district filtering
  const districtResults: SearchResultItem[] =
    query.length >= 2
      ? districts
          .filter(
            (d) =>
              d.nameEn.toLowerCase().includes(query.toLowerCase()) ||
              d.nameUr?.includes(query),
          )
          .slice(0, 6)
          .map((d) => ({
            pcode: d.pcode,
            name: d.nameEn,
            type: 'district' as const,
          }))
      : [];

  // Merge: districts first, then backend results (deduplicated)
  const districtPcodes = new Set(districtResults.map((r) => r.pcode));
  const allResults = [
    ...districtResults,
    ...backendResults.filter((r) => !districtPcodes.has(r.pcode)).slice(0, 6),
  ];

  const handleSelect = useCallback(
    (result: SearchResultItem) => {
      setQuery(result.name);
      setIsOpen(false);
      onSelect?.(result);
    },
    [onSelect],
  );

  const handleClear = useCallback(() => {
    setQuery('');
    setIsOpen(false);
    setBackendResults([]);
    inputRef.current?.focus();
  }, []);

  return (
    <div className="relative w-full sm:w-72" data-tour-step="search">
      {/* Input */}
      <div
        className={cn(
          'flex items-center rounded-lg border bg-[#1E293B] px-3',
          isOpen && allResults.length > 0
            ? 'border-[#06B6D4] shadow-[0_0_0_2px_rgba(6,182,212,0.2)]'
            : 'border-[#334155]',
          'transition-default',
        )}
      >
        <Search className="h-4 w-4 text-[#94A3B8] shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="Search district, incident, or article..."
          className="w-full bg-transparent px-2 py-2 text-sm text-[#F8FAFC] placeholder-[#94A3B8] outline-none"
        />
        {query && (
          <button
            onClick={handleClear}
            className="text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && allResults.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 rounded-lg border border-[#334155] bg-[#1E293B] py-1 shadow-xl z-50 max-h-72 overflow-y-auto">
          {allResults.map((result, idx) => {
            const config = TYPE_CONFIG[result.type] ?? TYPE_CONFIG.district;
            return (
              <button
                key={`${result.type}-${result.pcode}-${idx}`}
                onClick={() => handleSelect(result)}
                className="flex w-full items-start gap-2 px-3 py-2 text-sm text-[#F8FAFC] hover:bg-[#334155] transition-default"
              >
                <span
                  className={cn(
                    'flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase shrink-0 mt-0.5',
                    config.bg,
                  )}
                >
                  {config.icon}
                  {result.type}
                </span>
                <div className="text-left min-w-0">
                  <span className="block truncate">{result.name}</span>
                  {result.snippet && (
                    <span className="block text-[10px] text-[#94A3B8] truncate">
                      {result.snippet}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
