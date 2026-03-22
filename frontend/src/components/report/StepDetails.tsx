'use client';

import React, { useRef } from 'react';
import { cn } from '@/lib/utils';
import { FileText, Upload, X } from 'lucide-react';
import type { ReportFormData } from './ReportForm';

interface StepDetailsProps {
  data: ReportFormData;
  onChange: (partial: Partial<ReportFormData>) => void;
}

const MAX_PHOTOS = 3;
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png']);

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function StepDetails({ data, onChange }: StepDetailsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [photoError, setPhotoError] = React.useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    setPhotoError(null);

    const incoming = Array.from(files);
    const totalCount = data.photos.length + incoming.length;

    if (totalCount > MAX_PHOTOS) {
      setPhotoError(`Maximum ${MAX_PHOTOS} photos allowed.`);
      return;
    }

    for (const file of incoming) {
      if (!ALLOWED_TYPES.has(file.type)) {
        setPhotoError(`"${file.name}" is not a valid format. Only JPG and PNG allowed.`);
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        setPhotoError(`"${file.name}" is too large (${formatFileSize(file.size)}). Maximum 5 MB.`);
        return;
      }
    }

    const newPhotos = [...data.photos, ...incoming];
    onChange({ photos: newPhotos });
    // Reset input so same file can be re-selected
    e.target.value = '';
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
          <p className="text-xs text-[#334155]">JPG, PNG up to 5MB each (max {MAX_PHOTOS})</p>
        </button>

        {photoError && (
          <p className="mt-2 text-xs text-[#EF4444]">{photoError}</p>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          aria-label="Upload photos"
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
                <span className="text-[#94A3B8] text-[10px]">({formatFileSize(file.size)})</span>
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
