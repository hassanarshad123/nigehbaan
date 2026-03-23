'use client';

import React from 'react';
import {
  AlertTriangle,
  Calendar,
  MapPin,
  Eye,
  Users,
  Shield,
  UserX,
  Baby,
  FileCheck,
  Gavel,
  Cpu,
  Tag,
} from 'lucide-react';
import { INCIDENT_TYPE_COLORS, INCIDENT_TYPE_LABELS } from '@/lib/incidentColors';
import type { IncidentType } from '@/types';

interface IncidentPopupProps {
  properties: Record<string, unknown>;
  onClose: () => void;
}

export function IncidentPopup({ properties, onClose }: IncidentPopupProps) {
  const incidentType = String(properties.incidentType ?? properties.incident_type ?? 'unknown');
  const subType = (properties.subType ?? properties.sub_type) as string | null;
  const district = String(properties.districtName ?? properties.district_name ?? 'Unknown');
  const year = String(properties.year ?? 'N/A');
  const source = String(properties.sourceType ?? properties.source_type ?? 'unknown');
  const victimCount = Number(properties.victimCount ?? properties.victim_count ?? 0);
  const victimAgeMin = properties.victimAgeMin ?? properties.victim_age_min;
  const victimAgeMax = properties.victimAgeMax ?? properties.victim_age_max;
  const perpetratorType = (properties.perpetratorType ?? properties.perpetrator_type) as string | null;
  const firRegistered = properties.firRegistered ?? properties.fir_registered;
  const conviction = properties.conviction;
  const confidence = properties.extractionConfidence ?? properties.extraction_confidence ?? properties.confidence;

  const typeColor = INCIDENT_TYPE_COLORS[incidentType as IncidentType] ?? '#EF4444';
  const typeLabel = INCIDENT_TYPE_LABELS[incidentType as IncidentType] ?? incidentType;

  const ageRange = (() => {
    if (victimAgeMin != null && victimAgeMax != null) {
      return victimAgeMin === victimAgeMax
        ? `${victimAgeMin} years`
        : `${victimAgeMin}–${victimAgeMax} years`;
    }
    if (victimAgeMin != null) return `${victimAgeMin}+ years`;
    if (victimAgeMax != null) return `up to ${victimAgeMax} years`;
    return null;
  })();

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] shadow-xl p-3 w-[min(300px,calc(100vw-2rem))]">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <AlertTriangle className="h-4 w-4" style={{ color: typeColor }} />
          <span className="text-sm font-semibold text-[#F8FAFC]">
            {typeLabel}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-[#94A3B8] hover:text-[#F8FAFC] text-xs transition-default p-2 min-h-[44px] min-w-[44px] flex items-center justify-center -m-2"
          aria-label="Close popup"
        >
          &times;
        </button>
      </div>

      {/* Details */}
      <div className="space-y-1.5 text-xs">
        {/* Sub-type */}
        {subType && (
          <div className="flex items-center gap-1.5">
            <Tag className="h-3 w-3 text-[#94A3B8]" />
            <span className="text-[#94A3B8] capitalize">{String(subType).replace(/_/g, ' ')}</span>
          </div>
        )}

        {/* Location */}
        <div className="flex items-center gap-1.5">
          <MapPin className="h-3 w-3 text-[#06B6D4]" />
          <span className="text-[#F8FAFC]">{district}</span>
        </div>

        {/* Year */}
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3 w-3 text-[#F59E0B]" />
          <span className="text-[#94A3B8]">{year}</span>
        </div>

        {/* Source */}
        <div className="flex items-center gap-1.5">
          <Eye className="h-3 w-3 text-[#94A3B8]" />
          <span className="text-[#94A3B8] capitalize">{source.replace(/_/g, ' ')}</span>
        </div>

        {/* Victim count */}
        {victimCount > 0 && (
          <div className="flex items-center gap-1.5">
            <Users className="h-3 w-3 text-[#EC4899]" />
            <span className="text-[#F8FAFC]">{victimCount} victim{victimCount > 1 ? 's' : ''}</span>
          </div>
        )}

        {/* Victim age range */}
        {ageRange && (
          <div className="flex items-center gap-1.5">
            <Baby className="h-3 w-3 text-[#EC4899]" />
            <span className="text-[#94A3B8]">{ageRange}</span>
          </div>
        )}

        {/* Perpetrator type */}
        {perpetratorType && (
          <div className="flex items-center gap-1.5">
            <UserX className="h-3 w-3 text-[#EF4444]" />
            <span className="text-[#94A3B8] capitalize">{String(perpetratorType).replace(/_/g, ' ')}</span>
          </div>
        )}

        {/* Divider for legal/confidence data */}
        {(firRegistered != null || conviction != null || confidence != null) && (
          <div className="border-t border-[#334155] my-1.5" />
        )}

        {/* FIR status */}
        {firRegistered != null && (
          <div className="flex items-center gap-1.5">
            <FileCheck className="h-3 w-3 text-[#06B6D4]" />
            <span className="text-[#94A3B8]">FIR Filed:</span>
            <span className={firRegistered ? 'text-[#10B981]' : 'text-[#EF4444]'}>
              {firRegistered ? 'Yes' : 'No'}
            </span>
          </div>
        )}

        {/* Conviction */}
        {conviction != null && (
          <div className="flex items-center gap-1.5">
            <Gavel className="h-3 w-3 text-[#10B981]" />
            <span className="text-[#94A3B8]">Conviction:</span>
            <span className={conviction ? 'text-[#10B981]' : 'text-[#EF4444]'}>
              {conviction ? 'Yes' : 'No'}
            </span>
          </div>
        )}

        {/* AI confidence */}
        {confidence != null && (
          <div className="flex items-center gap-1.5">
            <Cpu className="h-3 w-3 text-[#8B5CF6]" />
            <span className="text-[#94A3B8]">AI Confidence:</span>
            <span className="text-[#94A3B8]">{(Number(confidence) * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}
