'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useWelcomeStore } from '@/stores/welcomeStore';

interface TourStep {
  target: string;
  title: string;
  description: string;
}

const TOUR_STEPS: TourStep[] = [
  {
    target: 'incidents',
    title: 'Incident Map',
    description:
      'Each dot is a reported incident of child trafficking. Click for details.',
  },
  {
    target: 'layers',
    title: 'Layer Controls',
    description:
      'Toggle brick kilns, borders, trafficking routes, and vulnerability data.',
  },
  {
    target: 'timeline',
    title: 'Time Slider',
    description:
      'Filter by year to see how patterns have changed over time.',
  },
  {
    target: 'search',
    title: 'Search',
    description:
      'Search any district for its risk profile and incident history.',
  },
];

interface SpotlightRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

function getTargetRect(target: string): SpotlightRect | null {
  const el = document.querySelector(`[data-tour-step="${target}"]`);
  if (!el) return null;
  const rect = el.getBoundingClientRect();
  const padding = 8;
  return {
    top: rect.top - padding,
    left: rect.left - padding,
    width: rect.width + padding * 2,
    height: rect.height + padding * 2,
  };
}

function getTooltipPosition(
  rect: SpotlightRect,
  windowWidth: number,
  windowHeight: number,
): { top: number; left: number; placement: 'top' | 'bottom' | 'left' | 'right' } {
  const tooltipW = 280;
  const tooltipH = 120;
  const gap = 12;

  // Try below
  if (rect.top + rect.height + gap + tooltipH < windowHeight) {
    return {
      top: rect.top + rect.height + gap,
      left: Math.max(8, Math.min(rect.left, windowWidth - tooltipW - 8)),
      placement: 'bottom',
    };
  }
  // Try above
  if (rect.top - gap - tooltipH > 0) {
    return {
      top: rect.top - gap - tooltipH,
      left: Math.max(8, Math.min(rect.left, windowWidth - tooltipW - 8)),
      placement: 'top',
    };
  }
  // Try right
  if (rect.left + rect.width + gap + tooltipW < windowWidth) {
    return {
      top: Math.max(8, rect.top),
      left: rect.left + rect.width + gap,
      placement: 'right',
    };
  }
  // Fallback: left
  return {
    top: Math.max(8, rect.top),
    left: Math.max(8, rect.left - gap - tooltipW),
    placement: 'left',
  };
}

export function MapTour() {
  const completeTour = useWelcomeStore((s) => s.completeTour);
  const [step, setStep] = useState(0);
  const [rect, setRect] = useState<SpotlightRect | null>(null);

  const currentStep = TOUR_STEPS[step];

  const measureTarget = useCallback(() => {
    if (!currentStep) return;
    const r = getTargetRect(currentStep.target);
    setRect(r);
  }, [currentStep]);

  useEffect(() => {
    measureTarget();
    window.addEventListener('resize', measureTarget);
    // Recalculate periodically in case elements load late
    const interval = setInterval(measureTarget, 500);
    return () => {
      window.removeEventListener('resize', measureTarget);
      clearInterval(interval);
    };
  }, [measureTarget]);

  const handleNext = useCallback(() => {
    if (step < TOUR_STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      completeTour();
    }
  }, [step, completeTour]);

  const handleSkip = useCallback(() => {
    completeTour();
  }, [completeTour]);

  if (!rect) {
    // Target not found yet — skip silently after a grace period
    return null;
  }

  const windowW = typeof window !== 'undefined' ? window.innerWidth : 1024;
  const windowH = typeof window !== 'undefined' ? window.innerHeight : 768;
  const tooltip = getTooltipPosition(rect, windowW, windowH);

  return (
    <div className="fixed inset-0 z-[70]" aria-label="Map tour" role="dialog">
      {/* Dark overlay with spotlight cutout using CSS clip-path */}
      <div
        className="absolute inset-0 bg-black/60 transition-all duration-300"
        style={{
          clipPath: `polygon(
            0% 0%, 0% 100%,
            ${rect.left}px 100%,
            ${rect.left}px ${rect.top}px,
            ${rect.left + rect.width}px ${rect.top}px,
            ${rect.left + rect.width}px ${rect.top + rect.height}px,
            ${rect.left}px ${rect.top + rect.height}px,
            ${rect.left}px 100%,
            100% 100%, 100% 0%
          )`,
        }}
        onClick={handleSkip}
      />

      {/* Spotlight border */}
      <div
        className="absolute border-2 border-[#06B6D4]/50 rounded-lg pointer-events-none transition-all duration-300"
        style={{
          top: rect.top,
          left: rect.left,
          width: rect.width,
          height: rect.height,
        }}
      />

      {/* Tooltip */}
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          className="absolute w-[280px] rounded-lg border border-[#334155] bg-[#1E293B]/95 backdrop-blur-md p-4 shadow-xl"
          style={{ top: tooltip.top, left: tooltip.left }}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
        >
          <p className="text-xs font-medium text-[#06B6D4] uppercase tracking-wider mb-1">
            Step {step + 1} of {TOUR_STEPS.length}
          </p>
          <h3 className="text-sm font-semibold text-[#F8FAFC] mb-1">
            {currentStep.title}
          </h3>
          <p className="text-sm text-[#94A3B8] leading-relaxed">
            {currentStep.description}
          </p>

          <div className="flex items-center justify-between mt-4">
            <button
              onClick={handleSkip}
              className="min-h-[44px] px-3 py-2 text-xs text-[#94A3B8] hover:text-[#F8FAFC] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#06B6D4] rounded"
            >
              Skip Tour
            </button>
            <button
              onClick={handleNext}
              className="min-h-[44px] px-4 py-2 text-xs font-medium rounded-md bg-[#06B6D4] text-[#0F172A] hover:bg-[#22D3EE] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#06B6D4]"
            >
              {step < TOUR_STEPS.length - 1 ? 'Next' : 'Done'}
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
