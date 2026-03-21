'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ChildSilhouetteProps {
  reducedMotion?: boolean;
}

const drawTransition = (delay: number, reducedMotion: boolean) =>
  reducedMotion
    ? { duration: 0 }
    : { duration: 1.0, delay, ease: [0.33, 1, 0.68, 1] as const };

export function ChildSilhouette({ reducedMotion = false }: ChildSilhouetteProps) {
  return (
    <svg
      viewBox="0 0 120 200"
      fill="none"
      className="w-24 h-36 sm:w-32 sm:h-48"
      aria-hidden="true"
    >
      {/* Head */}
      <motion.circle
        cx="60"
        cy="40"
        r="18"
        stroke="#F8FAFC"
        strokeWidth="1.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={drawTransition(0, reducedMotion)}
      />
      {/* Body */}
      <motion.path
        d="M60 58 L60 120"
        stroke="#F8FAFC"
        strokeWidth="1.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={drawTransition(0.15, reducedMotion)}
      />
      {/* Left arm */}
      <motion.path
        d="M60 75 L35 100"
        stroke="#F8FAFC"
        strokeWidth="1.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={drawTransition(0.3, reducedMotion)}
      />
      {/* Right arm */}
      <motion.path
        d="M60 75 L85 100"
        stroke="#F8FAFC"
        strokeWidth="1.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={drawTransition(0.35, reducedMotion)}
      />
      {/* Left leg */}
      <motion.path
        d="M60 120 L38 170"
        stroke="#F8FAFC"
        strokeWidth="1.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={drawTransition(0.45, reducedMotion)}
      />
      {/* Right leg */}
      <motion.path
        d="M60 120 L82 170"
        stroke="#F8FAFC"
        strokeWidth="1.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={drawTransition(0.5, reducedMotion)}
      />
    </svg>
  );
}
