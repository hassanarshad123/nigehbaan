import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines clsx + tailwind-merge for conditional, conflict-free class names.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number with commas (e.g. 7608 → "7,608").
 */
export function formatNumber(n: number): string {
  return n.toLocaleString('en-US');
}

/**
 * Clamp a value between min and max.
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Risk score to color mapping.
 */
export function riskColor(score: number): string {
  if (score >= 75) return '#EF4444'; // alert red
  if (score >= 50) return '#F59E0B'; // amber
  if (score >= 25) return '#06B6D4'; // cyan
  return '#10B981'; // emerald
}
