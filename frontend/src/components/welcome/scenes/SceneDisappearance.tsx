'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

interface SceneDisappearanceProps {
  reducedMotion?: boolean;
}

// Pre-calculated particle positions for the fragmentation effect
function generateParticles(count: number) {
  const particles: Array<{
    id: number;
    startX: number;
    startY: number;
    endX: number;
    endY: number;
    delay: number;
    size: number;
  }> = [];

  for (let i = 0; i < count; i++) {
    const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5;
    const distance = 80 + Math.random() * 120;
    particles.push({
      id: i,
      startX: (Math.random() - 0.5) * 40,
      startY: (Math.random() - 0.5) * 60,
      endX: Math.cos(angle) * distance,
      endY: Math.sin(angle) * distance,
      delay: Math.random() * 0.3,
      size: 2 + Math.random() * 3,
    });
  }
  return particles;
}

export function SceneDisappearance({ reducedMotion = false }: SceneDisappearanceProps) {
  const particles = useMemo(() => generateParticles(35), []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reducedMotion ? 0 : 0.4 }}
    >
      {/* Text */}
      <motion.div
        className="text-center mb-8 z-10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: reducedMotion ? 0 : 0.5 }}
      >
        <h2 className="text-3xl sm:text-5xl font-bold text-[#F8FAFC] tracking-tight">
          Every 8 minutes
        </h2>
        <p className="mt-2 text-base sm:text-lg text-[#94A3B8]">
          a child goes missing in Pakistan
        </p>
      </motion.div>

      {/* Particle fragmentation */}
      {!reducedMotion && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {particles.map((p) => (
            <motion.div
              key={p.id}
              className="absolute rounded-full"
              style={{
                width: p.size,
                height: p.size,
              }}
              initial={{
                x: p.startX,
                y: p.startY,
                opacity: 0.8,
                backgroundColor: '#F59E0B',
              }}
              animate={{
                x: p.endX,
                y: p.endY,
                opacity: 0,
                backgroundColor: '#EF4444',
              }}
              transition={{
                duration: 1.2,
                delay: p.delay,
                ease: [0.25, 0.46, 0.45, 0.94],
              }}
            />
          ))}
        </div>
      )}

      {/* Dimming amber glow shifting to red */}
      <motion.div
        className="absolute w-4 h-4 rounded-full"
        initial={{
          backgroundColor: '#F59E0B',
          boxShadow: '0 0 30px 12px rgba(245,158,11,0.4)',
        }}
        animate={{
          backgroundColor: '#EF4444',
          boxShadow: '0 0 10px 4px rgba(239,68,68,0.2)',
          scale: 0.5,
          opacity: 0,
        }}
        transition={{ duration: reducedMotion ? 0 : 1.2, ease: 'easeOut' }}
      />
    </motion.div>
  );
}
