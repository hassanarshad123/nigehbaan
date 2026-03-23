'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { X, ExternalLink, Loader2 } from 'lucide-react';
import { INCIDENT_TYPE_COLORS } from '@/lib/incidentColors';

interface DistrictPopupProps {
  pcode: string;
  data: Record<string, unknown> | null;
  onClose: () => void;
}

function riskColor(score: number | null): string {
  if (score == null) return '#94A3B8';
  if (score >= 0.7) return '#EF4444';
  if (score >= 0.4) return '#F59E0B';
  return '#10B981';
}

export function DistrictPopup({ pcode, data, onClose }: DistrictPopupProps) {
  if (!data) {
    return (
      <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 shadow-2xl w-64 max-w-[calc(100vw-2rem)]">
        <div className="flex items-center justify-center gap-2 py-4">
          <Loader2 className="h-4 w-4 animate-spin text-[#94A3B8]" />
          <span className="text-xs text-[#94A3B8]">Loading...</span>
        </div>
      </div>
    );
  }

  const nameEn = String(data.nameEn ?? pcode);
  const nameUr = String(data.nameUr ?? '');
  const incidentCount = Number(data.incidentCount ?? 0);
  const riskScore = data.riskScore != null ? Number(data.riskScore) : null;
  const topTypes = (data.topTypes as { type: string; count: number }[]) ?? [];
  const color = riskColor(riskScore);

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 shadow-2xl w-64 max-w-[calc(100vw-2rem)]">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-[#F8FAFC]">{nameEn}</h3>
          {nameUr && <p className="font-urdu text-xs text-[#94A3B8]">{nameUr}</p>}
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#334155] transition-default min-h-[44px] min-w-[44px] flex items-center justify-center -m-2"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-3 mb-3">
        <div className="flex flex-col items-center rounded bg-[#0F172A] px-3 py-1.5">
          <span className="text-lg font-bold text-[#F8FAFC]">
            {incidentCount.toLocaleString()}
          </span>
          <span className="text-xs text-[#94A3B8]">Incidents</span>
        </div>
        {riskScore != null && (
          <div className="flex flex-col items-center rounded bg-[#0F172A] px-3 py-1.5">
            <span className="text-lg font-bold" style={{ color }}>
              {(riskScore * 100).toFixed(0)}
            </span>
            <span className="text-xs text-[#94A3B8]">Risk Score</span>
          </div>
        )}
      </div>

      {/* Top incident types */}
      {topTypes.length > 0 && (
        <div className="mb-3">
          <p className="text-xs uppercase tracking-wider text-[#94A3B8] mb-1">
            Top Incident Types
          </p>
          <div className="space-y-1">
            {topTypes.slice(0, 5).map((t) => (
              <div
                key={t.type}
                className="flex items-center justify-between text-xs text-[#F8FAFC]"
              >
                <span className="flex items-center gap-1.5">
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ backgroundColor: INCIDENT_TYPE_COLORS[t.type as keyof typeof INCIDENT_TYPE_COLORS] ?? '#94A3B8' }}
                  />
                  <span className="capitalize">{t.type.replace(/_/g, ' ')}</span>
                </span>
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
