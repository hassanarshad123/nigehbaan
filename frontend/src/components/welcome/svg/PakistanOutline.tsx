'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface PakistanOutlineProps {
  reducedMotion?: boolean;
  className?: string;
}

// Simplified Pakistan border outline (~80 path commands)
const PAKISTAN_PATH =
  'M 180 30 L 195 35 L 210 28 L 225 32 L 240 25 L 255 30 ' +
  'L 268 22 L 280 28 L 290 35 L 298 45 L 305 55 L 310 68 ' +
  'L 315 80 L 318 95 L 320 110 L 318 125 L 312 138 L 305 150 ' +
  'L 298 160 L 290 168 L 282 175 L 275 185 L 270 195 L 265 208 ' +
  'L 258 220 L 250 232 L 242 242 L 235 250 L 228 258 L 220 268 ' +
  'L 210 278 L 200 288 L 190 295 L 180 300 L 168 305 L 155 308 ' +
  'L 142 310 L 130 308 L 118 302 L 108 295 L 98 285 L 90 275 ' +
  'L 82 265 L 75 252 L 70 240 L 65 228 L 60 215 L 55 200 ' +
  'L 52 185 L 50 170 L 48 155 L 50 140 L 55 128 L 60 115 ' +
  'L 68 105 L 75 95 L 85 85 L 95 78 L 105 72 L 115 65 ' +
  'L 125 58 L 135 52 L 145 45 L 155 40 L 165 35 L 180 30 Z';

// Approximate positions of major cities for pulse markers
export const CITY_POSITIONS = [
  { x: 195, y: 118, name: 'Lahore' },
  { x: 148, y: 278, name: 'Karachi' },
  { x: 210, y: 80, name: 'Islamabad' },
  { x: 175, y: 148, name: 'Multan' },
  { x: 232, y: 68, name: 'Peshawar' },
  { x: 88, y: 188, name: 'Quetta' },
  { x: 188, y: 128, name: 'Faisalabad' },
  { x: 160, y: 258, name: 'Hyderabad' },
];

export function PakistanOutline({ reducedMotion = false, className }: PakistanOutlineProps) {
  return (
    <svg
      viewBox="0 0 370 340"
      fill="none"
      className={className ?? 'w-64 h-72 sm:w-80 sm:h-96'}
      aria-hidden="true"
    >
      <motion.path
        d={PAKISTAN_PATH}
        stroke="#06B6D4"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={
          reducedMotion
            ? { duration: 0 }
            : { duration: 1.2, ease: [0.33, 1, 0.68, 1] }
        }
      />
    </svg>
  );
}
