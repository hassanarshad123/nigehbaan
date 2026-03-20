'use client';

import React, { useState, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Search, X } from 'lucide-react';

interface SearchResult {
  pcode: string;
  name: string;
  type: 'district' | 'city';
}

// Mock data for autocomplete — replaced by API in production
const MOCK_RESULTS: SearchResult[] = [
  { pcode: 'PK-PB-LHR', name: 'Lahore', type: 'city' },
  { pcode: 'PK-SD-KHI', name: 'Karachi', type: 'city' },
  { pcode: 'PK-IS-ISB', name: 'Islamabad', type: 'city' },
  { pcode: 'PK-PB-RWP', name: 'Rawalpindi', type: 'district' },
  { pcode: 'PK-PB-FSD', name: 'Faisalabad', type: 'district' },
  { pcode: 'PK-PB-MUL', name: 'Multan', type: 'district' },
  { pcode: 'PK-KP-PSH', name: 'Peshawar', type: 'district' },
  { pcode: 'PK-BN-QTA', name: 'Quetta', type: 'district' },
  { pcode: 'PK-SD-HYD', name: 'Hyderabad', type: 'district' },
  { pcode: 'PK-PB-SGD', name: 'Sargodha', type: 'district' },
];

interface SearchBarProps {
  onSelect?: (result: SearchResult) => void;
}

export function SearchBar({ onSelect }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = query.length >= 2
    ? MOCK_RESULTS.filter((r) =>
        r.name.toLowerCase().includes(query.toLowerCase()),
      )
    : [];

  const handleSelect = useCallback(
    (result: SearchResult) => {
      setQuery(result.name);
      setIsOpen(false);
      onSelect?.(result);
    },
    [onSelect],
  );

  const handleClear = useCallback(() => {
    setQuery('');
    setIsOpen(false);
    inputRef.current?.focus();
  }, []);

  return (
    <div className="relative w-72">
      {/* Input */}
      <div
        className={cn(
          'flex items-center rounded-lg border bg-[#1E293B] px-3',
          isOpen && filtered.length > 0
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
          placeholder="Search district or city..."
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
      {isOpen && filtered.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 rounded-lg border border-[#334155] bg-[#1E293B] py-1 shadow-xl z-50">
          {filtered.map((result) => (
            <button
              key={result.pcode}
              onClick={() => handleSelect(result)}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[#F8FAFC] hover:bg-[#334155] transition-default"
            >
              <span
                className={cn(
                  'rounded px-1.5 py-0.5 text-[10px] font-medium uppercase',
                  result.type === 'city'
                    ? 'bg-[#06B6D4]/10 text-[#06B6D4]'
                    : 'bg-[#10B981]/10 text-[#10B981]',
                )}
              >
                {result.type}
              </span>
              <span>{result.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
