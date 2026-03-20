'use client';

import React from 'react';
import { riskColor } from '@/lib/utils';

interface RiskGaugeProps {
  score: number; // 0-100
  size?: number;
}

export function RiskGauge({ score, size = 140 }: RiskGaugeProps) {
  const color = riskColor(score);
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  // We use a 270-degree arc (3/4 circle)
  const arcLength = circumference * 0.75;
  const filledLength = (score / 100) * arcLength;
  const center = size / 2;

  return (
    <div className="flex flex-col items-center">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-[135deg]"
      >
        {/* Background arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#334155"
          strokeWidth={8}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />
        {/* Filled arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeDasharray={`${filledLength} ${circumference}`}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      {/* Score label overlaid in center */}
      <div
        className="flex flex-col items-center"
        style={{ marginTop: -(size / 2 + 10) }}
      >
        <span
          className="text-3xl font-bold tabular-nums"
          style={{ color }}
        >
          {score}
        </span>
        <span className="text-xs text-[#94A3B8]">/ 100</span>
      </div>

      <p className="text-xs font-medium text-[#94A3B8] mt-6">Risk Score</p>
    </div>
  );
}
