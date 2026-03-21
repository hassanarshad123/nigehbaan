'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CITY_POSITIONS } from '../svg/PakistanOutline';

interface SceneRevealProps {
  reducedMotion?: boolean;
  onExplore: () => void;
}

export function SceneReveal({ reducedMotion = false, onExplore }: SceneRevealProps) {
  const fast = reducedMotion;

  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: fast ? 0 : 0.4 }}
    >
      {/* Cyan radial sweep */}
      {!fast && (
        <motion.div
          className="absolute rounded-full pointer-events-none"
          style={{
            background:
              'radial-gradient(circle, rgba(6,182,212,0.15) 0%, rgba(6,182,212,0.05) 40%, transparent 70%)',
          }}
          initial={{ width: 0, height: 0, opacity: 0 }}
          animate={{ width: 800, height: 800, opacity: 1 }}
          transition={{ duration: 1.2, ease: [0.33, 1, 0.68, 1] }}
        />
      )}

      {/* City dots transitioning from red to cyan */}
      <svg
        viewBox="0 0 370 340"
        className="absolute w-48 h-56 sm:w-64 sm:h-72"
        aria-hidden="true"
      >
        {/* Pakistan outline (static) */}
        <motion.path
          d={
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
            'L 125 58 L 135 52 L 145 45 L 155 40 L 165 35 L 180 30 Z'
          }
          stroke="#06B6D4"
          strokeWidth="2"
          fill="none"
          opacity={0.6}
        />
        {CITY_POSITIONS.map((city, i) => (
          <motion.circle
            key={city.name}
            cx={city.x}
            cy={city.y}
            r="5"
            initial={{ fill: '#EF4444' }}
            animate={{ fill: '#06B6D4' }}
            transition={{
              duration: fast ? 0 : 0.4,
              delay: fast ? 0 : 0.2 + i * 0.1,
            }}
          />
        ))}
      </svg>

      {/* Brand text */}
      <div className="relative z-10 flex flex-col items-center text-center">
        <motion.h1
          className="font-urdu text-5xl sm:text-7xl text-[#06B6D4] leading-relaxed"
          style={{
            textShadow: '0 0 40px rgba(6,182,212,0.4), 0 0 80px rgba(6,182,212,0.2)',
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: fast ? 0 : 0.3, duration: fast ? 0 : 0.6 }}
        >
          نگہبان
        </motion.h1>

        <motion.p
          className="text-xl sm:text-2xl font-semibold text-[#F8FAFC] mt-1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: fast ? 0 : 0.6, duration: fast ? 0 : 0.5 }}
        >
          Nigehbaan
        </motion.p>

        <motion.p
          className="text-sm sm:text-base text-[#94A3B8] mt-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: fast ? 0 : 0.8, duration: fast ? 0 : 0.5 }}
        >
          Watching over Pakistan&apos;s children
        </motion.p>

        <motion.button
          onClick={onExplore}
          className="mt-8 px-8 py-3 min-h-[44px] rounded-lg bg-[#06B6D4] text-[#0F172A] font-semibold text-base hover:bg-[#22D3EE] transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#06B6D4] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0F172A]"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: fast ? 0 : 1.2, duration: fast ? 0 : 0.4 }}
        >
          Explore the Map &rarr;
        </motion.button>
      </div>
    </motion.div>
  );
}
