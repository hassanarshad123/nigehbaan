'use client';

import React, { useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CinematicIntro } from './CinematicIntro';
import { SkipButton } from './SkipButton';
import { useWelcomeStore } from '@/stores/welcomeStore';

export function WelcomeOverlay() {
  const completeIntro = useWelcomeStore((s) => s.completeIntro);
  const [exiting, setExiting] = useState(false);

  const handleComplete = useCallback(() => {
    setExiting(true);
    // Brief fade-out before unmounting
    setTimeout(() => {
      completeIntro();
    }, 400);
  }, [completeIntro]);

  return (
    <AnimatePresence>
      {!exiting && (
        <motion.div
          className="fixed inset-0 z-[100] bg-[#0F172A]"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4 }}
          aria-label="Welcome animation"
          role="dialog"
          aria-modal="true"
        >
          {/* Make page content behind inert while overlay is showing */}
          <CinematicIntro onComplete={handleComplete} />
          <SkipButton onClick={handleComplete} label="Skip" />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
