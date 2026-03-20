'use client';

import React, { useEffect, useRef, useState } from 'react';
import { formatNumber } from '@/lib/utils';
import { useMapData } from '@/hooks/useMapData';

interface CounterItem {
  label: string;
  target: number;
  suffix?: string;
}

function useAnimatedCounter(target: number, duration = 2000): number {
  const [value, setValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const rafId = useRef<number | null>(null);

  useEffect(() => {
    startTime.current = null;

    const animate = (timestamp: number) => {
      if (startTime.current === null) {
        startTime.current = timestamp;
      }

      const elapsed = timestamp - startTime.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);

      setValue(Math.round(target * eased));

      if (progress < 1) {
        rafId.current = requestAnimationFrame(animate);
      }
    };

    rafId.current = requestAnimationFrame(animate);

    return () => {
      if (rafId.current !== null) {
        cancelAnimationFrame(rafId.current);
      }
    };
  }, [target, duration]);

  return value;
}

function CounterDisplay({ item }: { item: CounterItem }) {
  const animatedValue = useAnimatedCounter(item.target, 2500);

  return (
    <div className="flex flex-col">
      <span className="text-xl font-bold text-[#F8FAFC] tabular-nums">
        {formatNumber(animatedValue)}
        {item.suffix && <span className="text-sm ml-0.5">{item.suffix}</span>}
      </span>
      <span className="text-[11px] text-[#94A3B8]">{item.label}</span>
    </div>
  );
}

export function LiveCounter() {
  const { counts } = useMapData();

  const items: CounterItem[] = [
    { label: 'Documented incidents', target: counts.incidents },
    { label: 'Districts mapped', target: counts.boundaries },
    { label: 'Brick kilns tracked', target: counts.kilns },
    { label: 'Border crossings', target: counts.borders },
  ];

  return (
    <div className="rounded-lg border border-[#334155] bg-glass-surface p-3">
      <div className="flex items-center gap-6">
        {items.map((item) => (
          <CounterDisplay key={item.label} item={item} />
        ))}
      </div>
    </div>
  );
}
