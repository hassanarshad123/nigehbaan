'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { ReportType } from '@/types';
import {
  AlertTriangle,
  UserX,
  Hammer,
  HandCoins,
  Heart,
  HelpCircle,
} from 'lucide-react';

interface CategoryOption {
  value: ReportType;
  label: string;
  labelUr: string;
  icon: React.ReactNode;
  color: string;
}

const CATEGORIES: CategoryOption[] = [
  {
    value: 'suspicious_activity',
    label: 'Suspicious Activity',
    labelUr: 'مشکوک سرگرمی',
    icon: <AlertTriangle className="h-6 w-6" />,
    color: '#EF4444',
  },
  {
    value: 'missing_child',
    label: 'Missing Child',
    labelUr: 'لاپتہ بچہ',
    icon: <UserX className="h-6 w-6" />,
    color: '#F59E0B',
  },
  {
    value: 'bonded_labor',
    label: 'Bonded Labor',
    labelUr: 'بندھوا مزدوری',
    icon: <Hammer className="h-6 w-6" />,
    color: '#F97316',
  },
  {
    value: 'begging_ring',
    label: 'Begging Ring',
    labelUr: 'بھیک مانگنے کا نیٹ ورک',
    icon: <HandCoins className="h-6 w-6" />,
    color: '#06B6D4',
  },
  {
    value: 'child_marriage',
    label: 'Child Marriage',
    labelUr: 'کم عمری کی شادی',
    icon: <Heart className="h-6 w-6" />,
    color: '#EC4899',
  },
  {
    value: 'other',
    label: 'Other',
    labelUr: 'دیگر',
    icon: <HelpCircle className="h-6 w-6" />,
    color: '#94A3B8',
  },
];

interface StepCategoryProps {
  selected: ReportType | null;
  onSelect: (category: ReportType) => void;
}

export function StepCategory({ selected, onSelect }: StepCategoryProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[#F8FAFC] mb-1">
        What type of incident are you reporting?
      </h2>
      <p className="text-sm text-[#94A3B8] mb-6">
        Select the category that best describes what you observed.
      </p>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {CATEGORIES.map((cat) => {
          const isSelected = selected === cat.value;
          return (
            <button
              key={cat.value}
              onClick={() => onSelect(cat.value)}
              className={cn(
                'flex flex-col items-center gap-2 rounded-lg border p-4 transition-default',
                isSelected
                  ? 'border-[#06B6D4] bg-[#06B6D4]/10'
                  : 'border-[#334155] bg-[#0F172A] hover:border-[#94A3B8]',
              )}
            >
              <div style={{ color: cat.color }}>{cat.icon}</div>
              <span className="text-sm font-medium text-[#F8FAFC]">{cat.label}</span>
              <span className="font-urdu text-xs text-[#94A3B8]">{cat.labelUr}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
