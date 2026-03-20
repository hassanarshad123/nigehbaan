'use client';

import React from 'react';
import {
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import type { DistrictVulnerability } from '@/lib/api';

const COLORS = ['#06B6D4', '#EF4444', '#F59E0B', '#10B981'];

interface RadarChartProps {
  districts: {
    pcode: string;
    nameEn: string;
    vulnerability: DistrictVulnerability;
  }[];
}

interface RadarPoint {
  indicator: string;
  [key: string]: string | number;
}

function normalize(value: number | null, max: number): number {
  if (value == null) return 0;
  return Math.min(Math.max(value / max, 0), 1);
}

export function ComparisonRadarChart({ districts }: RadarChartProps) {
  const indicators: { key: keyof DistrictVulnerability; label: string; max: number }[] = [
    { key: 'literacyRate', label: 'Literacy', max: 100 },
    { key: 'povertyHeadcount', label: 'Poverty', max: 100 },
    { key: 'childLaborRate', label: 'Child Labor', max: 50 },
    { key: 'outOfSchoolRate', label: 'Out of School', max: 100 },
    { key: 'childMarriageRate', label: 'Child Marriage', max: 50 },
    { key: 'foodInsecurity', label: 'Food Insecurity', max: 100 },
    { key: 'kilnDensity', label: 'Kiln Density', max: 10 },
    { key: 'incidentRate', label: 'Incident Rate', max: 100 },
  ];

  const data: RadarPoint[] = indicators.map((ind) => {
    const point: RadarPoint = { indicator: ind.label };
    for (const d of districts) {
      const raw = d.vulnerability[ind.key];
      point[d.pcode] = normalize(raw as number | null, ind.max);
    }
    return point;
  });

  if (districts.length === 0) return null;

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
      <h3 className="text-sm font-semibold text-[#F8FAFC] mb-4">Vulnerability Radar</h3>
      <div className="h-72 sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsRadar data={data} cx="50%" cy="50%" outerRadius="70%">
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis
              dataKey="indicator"
              tick={{ fill: '#94A3B8', fontSize: 10 }}
            />
            <PolarRadiusAxis
              angle={22.5}
              domain={[0, 1]}
              tick={false}
              axisLine={false}
            />
            {districts.map((d, i) => (
              <Radar
                key={d.pcode}
                name={d.nameEn}
                dataKey={d.pcode}
                stroke={COLORS[i % COLORS.length]}
                fill={COLORS[i % COLORS.length]}
                fillOpacity={0.15}
                strokeWidth={2}
              />
            ))}
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E293B',
                border: '1px solid #334155',
                borderRadius: '6px',
                fontSize: '12px',
              }}
              formatter={(value: number) => `${(value * 100).toFixed(0)}%`}
            />
            <Legend wrapperStyle={{ fontSize: '11px', color: '#94A3B8' }} />
          </RechartsRadar>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
