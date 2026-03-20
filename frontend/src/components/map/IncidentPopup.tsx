'use client';

import React from 'react';
import { AlertTriangle, Calendar, MapPin, Eye, Users, Shield } from 'lucide-react';

interface IncidentPopupProps {
  properties: Record<string, unknown>;
  onClose: () => void;
}

const TYPE_LABELS: Record<string, string> = {
  kidnapping: 'Kidnapping',
  child_trafficking: 'Child Trafficking',
  sexual_abuse: 'Sexual Abuse',
  sexual_exploitation: 'Sexual Exploitation',
  online_exploitation: 'Online Exploitation',
  child_labor: 'Child Labor',
  bonded_labor: 'Bonded Labor',
  child_marriage: 'Child Marriage',
  child_murder: 'Child Murder',
  honor_killing: 'Honor Killing',
  begging_ring: 'Begging Ring',
  organ_trafficking: 'Organ Trafficking',
  missing: 'Missing',
  physical_abuse: 'Physical Abuse',
  child_pornography: 'Child Pornography',
  other: 'Other',
};

export function IncidentPopup({ properties, onClose }: IncidentPopupProps) {
  const incidentType = String(properties.incidentType ?? properties.incident_type ?? 'unknown');
  const district = String(properties.districtName ?? properties.district_name ?? 'Unknown');
  const year = String(properties.year ?? 'N/A');
  const source = String(properties.sourceType ?? properties.source_type ?? 'unknown');
  const victimCount = Number(properties.victimCount ?? properties.victim_count ?? 0);
  const confidence = properties.confidence != null ? Number(properties.confidence) : null;

  return (
    <div className="rounded-lg border border-[#334155] bg-[#1E293B] shadow-xl p-3 w-[min(280px,calc(100vw-2rem))]">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <AlertTriangle className="h-4 w-4 text-[#EF4444]" />
          <span className="text-sm font-semibold text-[#F8FAFC]">
            {TYPE_LABELS[incidentType] ?? incidentType}
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
        <div className="flex items-center gap-1.5">
          <MapPin className="h-3 w-3 text-[#06B6D4]" />
          <span className="text-[#F8FAFC]">{district}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3 w-3 text-[#F59E0B]" />
          <span className="text-[#94A3B8]">{year}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Eye className="h-3 w-3 text-[#94A3B8]" />
          <span className="text-[#94A3B8] capitalize">{source.replace(/_/g, ' ')}</span>
        </div>
        {victimCount > 0 && (
          <div className="flex items-center gap-1.5">
            <Users className="h-3 w-3 text-[#EC4899]" />
            <span className="text-[#F8FAFC]">{victimCount} victim{victimCount > 1 ? 's' : ''}</span>
          </div>
        )}
        {confidence != null && (
          <div className="flex items-center gap-1.5">
            <Shield className="h-3 w-3 text-[#10B981]" />
            <span className="text-[#94A3B8]">{(confidence * 100).toFixed(0)}% confidence</span>
          </div>
        )}
      </div>
    </div>
  );
}
