'use client';

import React from 'react';
import Link from 'next/link';
import { cn, formatNumber, riskColor } from '@/lib/utils';
import { X, ExternalLink } from 'lucide-react';

interface DistrictPopupProps {
  pcode: string;
  name: string;
  nameUr: string;
  incidentCount: number;
  riskScore: number;
  topTypes: { type: string; count: number }[];
  onClose: () => void;
}

export function DistrictPopup({
  pcode,
  name,
  nameUr,
  incidentCount,
  riskScore,
  topTypes,
  onClose,
}: DistrictPopupProps) {
  const color = riskColor(riskScore);

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 shadow-2xl w-64 max-w-[calc(100vw-2rem)] animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-[#F8FAFC]">{name}</h3>
          <p className="font-urdu text-xs text-[#94A3B8]">{nameUr}</p>
        </div>
        <button
          onClick={onClose}
          className="rounded p-0.5 text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#334155] transition-default"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-3 mb-3">
        <div className="flex flex-col items-center rounded bg-[#0F172A] px-3 py-1.5">
          <span className="text-lg font-bold text-[#F8FAFC]">
            {formatNumber(incidentCount)}
          </span>
          <span className="text-[10px] text-[#94A3B8]">Incidents</span>
        </div>
        <div className="flex flex-col items-center rounded bg-[#0F172A] px-3 py-1.5">
          <span className="text-lg font-bold" style={{ color }}>
            {riskScore}
          </span>
          <span className="text-[10px] text-[#94A3B8]">Risk Score</span>
        </div>
      </div>

      {/* Top incident types */}
      {topTypes.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] uppercase tracking-wider text-[#94A3B8] mb-1">
            Top Incident Types
          </p>
          <div className="space-y-0.5">
            {topTypes.slice(0, 3).map((t) => (
              <div
                key={t.type}
                className="flex items-center justify-between text-xs text-[#F8FAFC]"
              >
                <span className="capitalize">{t.type.replace(/_/g, ' ')}</span>
                <span className="text-[#94A3B8]">{t.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View Profile link */}
      <Link
        href={`/district/${pcode}`}
        className={cn(
          'flex items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-medium',
          'bg-[#06B6D4]/10 text-[#06B6D4] hover:bg-[#06B6D4]/20 transition-default',
        )}
      >
        <span>View Profile</span>
        <ExternalLink className="h-3 w-3" />
      </Link>
    </div>
  );
}
