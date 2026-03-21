'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { PakistanOutline, CITY_POSITIONS } from '../svg/PakistanOutline';
import { AnimatedCounter } from '../AnimatedCounter';

interface SceneScaleProps {
  reducedMotion?: boolean;
}

export function SceneScale({ reducedMotion = false }: SceneScaleProps) {
  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reducedMotion ? 0 : 0.4 }}
    >
      <div className="relative flex flex-col items-center">
        {/* Pakistan outline with city pulses */}
        <div className="relative">
          <PakistanOutline reducedMotion={reducedMotion} className="w-48 h-56 sm:w-64 sm:h-72" />

          {/* City pulse markers */}
          <svg
            viewBox="0 0 370 340"
            className="absolute inset-0 w-48 h-56 sm:w-64 sm:h-72"
            aria-hidden="true"
          >
            {CITY_POSITIONS.map((city, i) => (
              <motion.circle
                key={city.name}
                cx={city.x}
                cy={city.y}
                r="5"
                fill="#EF4444"
                initial={{ opacity: 0, scale: 0 }}
                animate={{
                  opacity: [0, 0.8, 0.4],
                  scale: [0, 1.5, 1],
                }}
                transition={
                  reducedMotion
                    ? { duration: 0 }
                    : {
                        duration: 0.6,
                        delay: 0.3 + i * 0.08,
                        ease: 'easeOut',
                      }
                }
              />
            ))}
          </svg>
        </div>

        {/* Stats */}
        <motion.div
          className="mt-6 text-center"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: reducedMotion ? 0 : 0.5, duration: reducedMotion ? 0 : 0.5 }}
        >
          <div className="flex flex-wrap items-baseline justify-center gap-x-2 text-lg sm:text-2xl">
            <AnimatedCounter
              target={12000}
              duration={reducedMotion ? 0 : 1200}
              suffix="+"
              className="font-bold text-[#EF4444] tabular-nums"
            />
            <span className="text-[#94A3B8]">incidents across</span>
            <AnimatedCounter
              target={160}
              duration={reducedMotion ? 0 : 1000}
              className="font-bold text-[#06B6D4] tabular-nums"
            />
            <span className="text-[#94A3B8]">districts</span>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
