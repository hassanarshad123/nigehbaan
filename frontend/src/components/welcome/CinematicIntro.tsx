'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { SceneChild } from './scenes/SceneChild';
import { SceneDisappearance } from './scenes/SceneDisappearance';
import { SceneScale } from './scenes/SceneScale';
import { SceneReveal } from './scenes/SceneReveal';
import { useReducedMotion } from '@/hooks/useReducedMotion';

interface CinematicIntroProps {
  onComplete: () => void;
}

export function CinematicIntro({ onComplete }: CinematicIntroProps) {
  const [scene, setScene] = useState(1);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion) {
      // With reduced motion, go straight to the reveal
      setScene(4);
      return;
    }

    const timers = [
      setTimeout(() => setScene(2), 1500),
      setTimeout(() => setScene(3), 3000),
      setTimeout(() => setScene(4), 4500),
    ];

    return () => timers.forEach(clearTimeout);
  }, [reducedMotion]);

  const handleExplore = useCallback(() => {
    onComplete();
  }, [onComplete]);

  return (
    <div className="relative w-full h-full">
      <AnimatePresence mode="sync">
        {scene === 1 && <SceneChild key="child" reducedMotion={reducedMotion} />}
        {scene === 2 && (
          <SceneDisappearance key="disappear" reducedMotion={reducedMotion} />
        )}
        {scene === 3 && <SceneScale key="scale" reducedMotion={reducedMotion} />}
        {scene >= 4 && (
          <SceneReveal
            key="reveal"
            reducedMotion={reducedMotion}
            onExplore={handleExplore}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
