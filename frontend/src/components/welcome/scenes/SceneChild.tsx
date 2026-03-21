'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ChildSilhouette } from '../svg/ChildSilhouette';

interface SceneChildProps {
  reducedMotion?: boolean;
}

export function SceneChild({ reducedMotion = false }: SceneChildProps) {
  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reducedMotion ? 0 : 0.4 }}
    >
      {/* Amber glow dot */}
      <motion.div
        className="absolute"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={
          reducedMotion
            ? { duration: 0 }
            : { type: 'spring', stiffness: 200, damping: 20, delay: 0.1 }
        }
      >
        <div className="relative">
          {/* Glow pulse */}
          <motion.div
            className="absolute inset-0 rounded-full bg-[#F59E0B]"
            style={{ width: 16, height: 16, x: -8, y: -8 }}
            animate={
              reducedMotion
                ? {}
                : {
                    boxShadow: [
                      '0 0 20px 8px rgba(245,158,11,0.4)',
                      '0 0 40px 16px rgba(245,158,11,0.2)',
                      '0 0 20px 8px rgba(245,158,11,0.4)',
                    ],
                  }
            }
            transition={
              reducedMotion
                ? {}
                : { duration: 2, repeat: Infinity, ease: 'easeInOut' }
            }
          />
          {/* Core dot */}
          <div
            className="relative rounded-full bg-[#F59E0B]"
            style={{ width: 16, height: 16, marginLeft: -8, marginTop: -8 }}
          />
        </div>
      </motion.div>

      {/* Child silhouette draws in around the dot */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: reducedMotion ? 0 : 0.3, duration: reducedMotion ? 0 : 0.3 }}
      >
        <ChildSilhouette reducedMotion={reducedMotion} />
      </motion.div>
    </motion.div>
  );
}
