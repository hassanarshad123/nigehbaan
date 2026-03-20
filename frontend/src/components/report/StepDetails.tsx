'use client';

import React, { useRef } from 'react';
import { cn } from '@/lib/utils';
import { FileText, Upload, X } from 'lucide-react';
import type { ReportFormData } from './ReportForm';

interface StepDetailsProps {
  data: ReportFormData;
  onChange: (partial: Partial<ReportFormData>) => void;
}

export function StepDetails({ data, onChange }: StepDetailsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newPhotos = [...data.photos, ...Array.from(files)];
    onChange({ photos: newPhotos });
  };

  const removePhoto = (index: number) => {
    const newPhotos = data.photos.filter((_, i) => i !== index);
    onChange({ photos: newPhotos });
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-[#F8FAFC] mb-1">
        Describe what you observed
      </h2>
      <p className="text-sm text-[#94A3B8] mb-6">
        Provide as much detail as possible. This helps authorities investigate.
      </p>

      {/* Description textarea */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-[#94A3B8] mb-1.5">
          <FileText className="inline h-3.5 w-3.5 mr-1" />
          Description
        </label>
        <textarea
          value={data.description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Provide any details that may help..."
          rows={5}
          className={cn(
            'w-full rounded-md border border-[#334155] bg-[#0F172A] px-3 py-2.5 text-sm text-[#F8FAFC]',
            'placeholder-[#94A3B8] outline-none border-glow-focus transition-default resize-none',
          )}
        />
        <p className="mt-1 text-xs text-[#94A3B8]">
          {data.description.length} characters
          {data.description.length < 10 && ' (minimum 10)'}
        </p>
      </div>

      {/* Photo upload */}
      <div>
        <label className="block text-sm font-medium text-[#94A3B8] mb-1.5">
          <Upload className="inline h-3.5 w-3.5 mr-1" />
          Upload Photos (optional)
        </label>

        <button
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            'w-full rounded-md border border-dashed border-[#334155] bg-[#0F172A] px-4 py-6 text-center',
            'hover:border-[#06B6D4] transition-default',
          )}
        >
          <Upload className="mx-auto h-6 w-6 text-[#94A3B8] mb-1" />
          <p className="text-sm text-[#94A3B8]">Click to upload photos</p>
          <p className="text-xs text-[#334155]">JPG, PNG up to 10MB each</p>
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Photo previews */}
        {data.photos.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {data.photos.map((file, idx) => (
              <div
                key={`${file.name}-${idx}`}
                className="relative rounded-md border border-[#334155] bg-[#0F172A] px-3 py-1.5 text-xs text-[#F8FAFC] flex items-center gap-2"
              >
                <span className="truncate max-w-[120px]">{file.name}</span>
                <button
                  onClick={() => removePhoto(idx)}
                  className="text-[#94A3B8] hover:text-[#EF4444] transition-default"
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
