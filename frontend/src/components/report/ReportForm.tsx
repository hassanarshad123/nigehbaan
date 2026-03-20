'use client';

import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { StepCategory } from './StepCategory';
import { StepLocation } from './StepLocation';
import { StepWhen } from './StepWhen';
import { StepDetails } from './StepDetails';
import { StepContact } from './StepContact';
import type { ReportType } from '@/types';
import { ChevronLeft, ChevronRight, Send, Loader2 } from 'lucide-react';
import { submitPublicReport } from '@/lib/api';

const STEPS = ['Category', 'Location', 'When', 'Details', 'Contact'] as const;

export interface ReportFormData {
  category: ReportType | null;
  latitude: number | null;
  longitude: number | null;
  address: string;
  date: string;
  description: string;
  photos: File[];
  contactName: string;
  contactPhone: string;
  contactEmail: string;
  anonymous: boolean;
}

const INITIAL_DATA: ReportFormData = {
  category: null,
  latitude: null,
  longitude: null,
  address: '',
  date: '',
  description: '',
  photos: [],
  contactName: '',
  contactPhone: '',
  contactEmail: '',
  anonymous: true,
};

export function ReportForm() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [data, setData] = useState<ReportFormData>(INITIAL_DATA);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const updateData = useCallback(
    (partial: Partial<ReportFormData>) => {
      setData((prev) => ({ ...prev, ...partial }));
    },
    [],
  );

  const canProceed = (): boolean => {
    switch (step) {
      case 1:
        return data.category !== null;
      case 2:
        return data.address.length > 0 || (data.latitude !== null && data.longitude !== null);
      case 3:
        return data.date.length > 0;
      case 4:
        return data.description.length >= 10;
      case 5:
        return true;
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const response = await submitPublicReport({
        reportType: data.category!,
        description: data.description,
        latitude: data.latitude ?? undefined,
        longitude: data.longitude ?? undefined,
        reporterName: data.contactName || undefined,
        reporterContact: data.contactPhone || data.contactEmail || undefined,
        isAnonymous: data.anonymous,
      });
      const ref = (response as Record<string, unknown>).referenceNumber as string | undefined;
      router.push(`/report/success${ref ? `?ref=${encodeURIComponent(ref)}` : ''}`);
    } catch (err) {
      console.error('Report submission failed:', err);
      setSubmitError('Failed to submit report. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      {/* Progress indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {STEPS.map((label, idx) => {
            const stepNum = idx + 1;
            const isActive = stepNum === step;
            const isDone = stepNum < step;
            return (
              <div key={label} className="flex flex-col items-center gap-1">
                <div
                  className={cn(
                    'flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full text-xs font-semibold transition-default',
                    isActive && 'bg-[#06B6D4] text-[#0F172A]',
                    isDone && 'bg-[#10B981] text-[#0F172A]',
                    !isActive && !isDone && 'bg-[#334155] text-[#94A3B8]',
                  )}
                >
                  {isDone ? '\u2713' : stepNum}
                </div>
                <span
                  className={cn(
                    'text-[10px] hidden sm:block',
                    isActive ? 'text-[#F8FAFC]' : 'text-[#94A3B8]',
                  )}
                >
                  {label}
                </span>
              </div>
            );
          })}
        </div>
        {/* Mobile step label */}
        <p className="sm:hidden text-center text-xs text-[#94A3B8] mt-2">
          Step {step}: {STEPS[step - 1]}
        </p>
        {/* Progress bar */}
        <div className="h-1 rounded-full bg-[#334155]">
          <div
            className="h-1 rounded-full bg-[#06B6D4] transition-all duration-300"
            style={{ width: `${((step - 1) / (STEPS.length - 1)) * 100}%` }}
          />
        </div>
      </div>

      {/* Step content */}
      <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 sm:p-6 mb-6">
        {step === 1 && <StepCategory selected={data.category} onSelect={(c) => updateData({ category: c })} />}
        {step === 2 && <StepLocation data={data} onChange={updateData} />}
        {step === 3 && <StepWhen date={data.date} onChange={(date) => updateData({ date })} />}
        {step === 4 && <StepDetails data={data} onChange={updateData} />}
        {step === 5 && <StepContact data={data} onChange={updateData} />}
      </div>

      {/* Error message */}
      {submitError && (
        <div className="mb-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {submitError}
        </div>
      )}

      {/* Navigation buttons */}
      <div className="flex justify-between">
        <button
          onClick={() => setStep((s) => Math.max(1, s - 1))}
          disabled={step === 1}
          className={cn(
            'flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-default',
            step === 1
              ? 'text-[#334155] cursor-not-allowed'
              : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
          )}
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </button>

        {step < STEPS.length ? (
          <button
            onClick={() => setStep((s) => Math.min(STEPS.length, s + 1))}
            disabled={!canProceed()}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-default',
              canProceed()
                ? 'bg-[#06B6D4] text-[#0F172A] hover:bg-[#06B6D4]/90'
                : 'bg-[#334155] text-[#94A3B8] cursor-not-allowed',
            )}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-default',
              'bg-[#10B981] text-[#0F172A] hover:bg-[#10B981]/90',
              isSubmitting && 'opacity-60 cursor-not-allowed',
            )}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                Submit Report
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
