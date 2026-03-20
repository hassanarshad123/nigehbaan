'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { ShieldCheck, User, Phone, Mail } from 'lucide-react';
import type { ReportFormData } from './ReportForm';

interface StepContactProps {
  data: ReportFormData;
  onChange: (partial: Partial<ReportFormData>) => void;
}

export function StepContact({ data, onChange }: StepContactProps) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[#F8FAFC] mb-1">
        Contact Information
      </h2>
      <p className="text-sm text-[#94A3B8] mb-6">
        Optional. Providing contact info allows authorities to follow up if needed.
      </p>

      {/* Anonymous toggle */}
      <div className="mb-6 rounded-lg border border-[#334155] bg-[#0F172A] p-4">
        <label className="flex items-center gap-3 cursor-pointer">
          <div className="relative">
            <input
              type="checkbox"
              checked={data.anonymous}
              onChange={(e) => onChange({ anonymous: e.target.checked })}
              className="sr-only"
            />
            <div
              className={cn(
                'h-6 w-11 rounded-full transition-default',
                data.anonymous ? 'bg-[#10B981]' : 'bg-[#334155]',
              )}
            >
              <div
                className={cn(
                  'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
                  data.anonymous ? 'translate-x-[22px]' : 'translate-x-0.5',
                )}
              />
            </div>
          </div>
          <div>
            <span className="flex items-center gap-1.5 text-sm font-medium text-[#F8FAFC]">
              <ShieldCheck className="h-4 w-4 text-[#10B981]" />
              Report Anonymously
            </span>
            <p className="text-xs text-[#94A3B8] mt-0.5">
              Your identity will not be stored or shared.
            </p>
          </div>
        </label>
      </div>

      {/* Contact fields (shown when not anonymous) */}
      {!data.anonymous && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#94A3B8] mb-1.5">
              <User className="inline h-3.5 w-3.5 mr-1" />
              Your Name
            </label>
            <input
              type="text"
              value={data.contactName}
              onChange={(e) => onChange({ contactName: e.target.value })}
              placeholder="Your name"
              className={cn(
                'w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2.5 text-sm text-[#F8FAFC]',
                'placeholder-[#94A3B8] outline-none border-glow-focus transition-default',
              )}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#94A3B8] mb-1.5">
              <Phone className="inline h-3.5 w-3.5 mr-1" />
              Phone Number
            </label>
            <input
              type="tel"
              value={data.contactPhone}
              onChange={(e) => onChange({ contactPhone: e.target.value })}
              placeholder="03XX-XXXXXXX"
              className={cn(
                'w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2.5 text-sm text-[#F8FAFC]',
                'placeholder-[#94A3B8] outline-none border-glow-focus transition-default',
              )}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#94A3B8] mb-1.5">
              <Mail className="inline h-3.5 w-3.5 mr-1" />
              Email Address
            </label>
            <input
              type="email"
              value={data.contactEmail}
              onChange={(e) => onChange({ contactEmail: e.target.value })}
              placeholder="you@example.com"
              className={cn(
                'w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2.5 text-sm text-[#F8FAFC]',
                'placeholder-[#94A3B8] outline-none border-glow-focus transition-default',
              )}
            />
          </div>
        </div>
      )}
    </div>
  );
}
