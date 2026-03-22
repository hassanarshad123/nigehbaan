'use client';

import React from 'react';
import type { DistrictVulnerability } from '@/lib/api';
import { cn } from '@/lib/utils';

interface ComparisonTableProps {
  districts: {
    pcode: string;
    nameEn: string;
    vulnerability: DistrictVulnerability;
  }[];
}

const ROWS: { key: keyof DistrictVulnerability; label: string; format: (v: number | null) => string }[] = [
  { key: 'literacyRate', label: 'Literacy Rate', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'childLaborRate', label: 'Child Labor Rate', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'povertyHeadcount', label: 'Poverty Headcount', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'foodInsecurity', label: 'Food Insecurity', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'outOfSchoolRate', label: 'Out of School', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'childMarriageRate', label: 'Child Marriage', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'enrollmentRate', label: 'Enrollment Rate', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'kilnDensity', label: 'Kiln Density', format: (v) => v != null ? v.toFixed(2) : 'N/A' },
  { key: 'borderDistanceKm', label: 'Border Distance', format: (v) => v != null ? `${v.toFixed(0)} km` : 'N/A' },
  { key: 'floodExposure', label: 'Flood Exposure', format: (v) => v != null ? `${(v * 100).toFixed(0)}%` : 'N/A' },
  { key: 'incidentRate', label: 'Incident Rate', format: (v) => v != null ? v.toFixed(1) : 'N/A' },
  { key: 'convictionRate', label: 'Conviction Rate', format: (v) => v != null ? `${v.toFixed(1)}%` : 'N/A' },
  { key: 'traffickingRiskScore', label: 'Risk Score', format: (v) => v != null ? `${(v * 100).toFixed(0)}%` : 'N/A' },
];

export function ComparisonTable({ districts }: ComparisonTableProps) {
  if (districts.length === 0) return null;

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
      {/* Desktop table */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#334155]">
              <th className="px-4 py-3 text-left text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
                Indicator
              </th>
              {districts.map((d) => (
                <th
                  key={d.pcode}
                  className="px-4 py-3 text-right text-xs font-medium text-[#06B6D4] uppercase tracking-wider"
                >
                  {d.nameEn}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr
                key={row.key}
                className="border-b border-[#334155]/50 hover:bg-[#334155]/20 transition-colors"
              >
                <td className="px-4 py-2.5 text-[#94A3B8] text-xs">{row.label}</td>
                {districts.map((d) => {
                  const val = d.vulnerability[row.key] as number | null;
                  return (
                    <td key={d.pcode} className="px-4 py-2.5 text-right text-[#F8FAFC] tabular-nums text-xs">
                      {row.format(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card view */}
      <div className="sm:hidden divide-y divide-[#334155]/50">
        {districts.map((d) => (
          <div key={d.pcode} className="p-4">
            <h4 className="text-sm font-semibold text-[#06B6D4] mb-3">{d.nameEn}</h4>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              {ROWS.map((row) => {
                const val = d.vulnerability[row.key] as number | null;
                return (
                  <div key={row.key} className="flex flex-col">
                    <span className="text-xs text-[#94A3B8] uppercase tracking-wider">{row.label}</span>
                    <span className="text-xs text-[#F8FAFC] tabular-nums">{row.format(val)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
