'use client';

import React from 'react';
import { formatNumber } from '@/lib/utils';
import { Users, AlertTriangle, Factory, GraduationCap, Scale } from 'lucide-react';

interface DistrictStatsProps {
  population: number;
  incidentCount: number;
  kilnCount: number;
  schoolCount: number;
  convictionRate: number;
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  return (
    <div className="rounded-lg border border-[#334155] bg-[#0F172A] p-3">
      <div className="flex items-center gap-2 mb-2">
        <div style={{ color }}>{icon}</div>
        <span className="text-xs text-[#94A3B8]">{label}</span>
      </div>
      <p className="text-lg font-bold text-[#F8FAFC] tabular-nums">{value}</p>
    </div>
  );
}

export function DistrictStats({
  population,
  incidentCount,
  kilnCount,
  schoolCount,
  convictionRate,
}: DistrictStatsProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <StatCard
        icon={<Users className="h-4 w-4" />}
        label="Population"
        value={formatNumber(population)}
        color="#06B6D4"
      />
      <StatCard
        icon={<AlertTriangle className="h-4 w-4" />}
        label="Incidents"
        value={formatNumber(incidentCount)}
        color="#EF4444"
      />
      <StatCard
        icon={<Factory className="h-4 w-4" />}
        label="Brick Kilns"
        value={formatNumber(kilnCount)}
        color="#F97316"
      />
      <StatCard
        icon={<GraduationCap className="h-4 w-4" />}
        label="Schools"
        value={formatNumber(schoolCount)}
        color="#10B981"
      />
      <StatCard
        icon={<Scale className="h-4 w-4" />}
        label="Conviction Rate"
        value={`${convictionRate.toFixed(1)}%`}
        color="#F59E0B"
      />
    </div>
  );
}
