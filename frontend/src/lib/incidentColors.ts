/**
 * Canonical incident type → color mapping.
 * Used by MapContainer (data-driven circle paint), MapLegend, FilterDrawer, and IncidentPopup.
 */

import type { IncidentType } from '@/types';

export const INCIDENT_TYPE_COLORS: Record<IncidentType, string> = {
  kidnapping: '#EF4444',
  child_trafficking: '#DC2626',
  sexual_abuse: '#EC4899',
  sexual_exploitation: '#BE185D',
  online_exploitation: '#6366F1',
  child_labor: '#D97706',
  bonded_labor: '#F97316',
  child_marriage: '#F59E0B',
  child_murder: '#991B1B',
  honor_killing: '#7F1D1D',
  begging_ring: '#8B5CF6',
  organ_trafficking: '#6B21A8',
  missing: '#3B82F6',
  physical_abuse: '#FB7185',
  child_pornography: '#4F46E5',
  abandonment: '#78716C',
  medical_negligence: '#57534E',
  other: '#94A3B8',
};

export const INCIDENT_TYPE_LABELS: Record<IncidentType, string> = {
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
  abandonment: 'Abandonment',
  medical_negligence: 'Medical Negligence',
  other: 'Other',
};

/**
 * Build a MapLibre `match` expression for data-driven circle-color.
 * Evaluates per-feature: reads `incidentType` property and returns the matching color.
 */
export function buildIncidentColorExpression(): unknown[] {
  const entries: string[] = [];
  for (const [type, color] of Object.entries(INCIDENT_TYPE_COLORS)) {
    entries.push(type, color);
  }
  // ['match', ['get', 'incidentType'], 'kidnapping', '#EF4444', ..., '#94A3B8']
  return ['match', ['get', 'incidentType'], ...entries, '#94A3B8'];
}
