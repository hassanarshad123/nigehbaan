'use client';

import React, { useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Header } from '@/components/layout/Header';
import { LiveCounter } from '@/components/map/LiveCounter';
import { SearchBar } from '@/components/map/SearchBar';
import { MobileMapControls } from '@/components/map/MobileMapControls';
import { TimeSlider } from '@/components/map/TimeSlider';
import { useWelcomeStore } from '@/stores/welcomeStore';

const MapContainer = dynamic(
  () => import('@/components/map/MapContainer').then((mod) => mod.MapContainer),
  { ssr: false },
);

const WelcomeOverlay = dynamic(
  () => import('@/components/welcome/WelcomeOverlay').then((m) => m.WelcomeOverlay),
  { ssr: false },
);

const MapTour = dynamic(
  () => import('@/components/welcome/MapTour').then((m) => m.MapTour),
  { ssr: false },
);

export default function HomePage() {
  const mounted = useWelcomeStore((s) => s.mounted);
  const hasSeenIntro = useWelcomeStore((s) => s.hasSeenIntro);
  const hasSeenTour = useWelcomeStore((s) => s.hasSeenTour);
  const setMounted = useWelcomeStore((s) => s.setMounted);

  useEffect(() => {
    setMounted();
  }, [setMounted]);

  return (
    <div className="relative h-screen w-screen overflow-hidden">
      {/* Full-screen map */}
      <MapContainer />

      {/* Header overlay — z-50 */}
      <Header />

      {/* Search bar — top center below header — z-30 */}
      <div className="absolute top-16 left-2 right-14 sm:left-1/2 sm:right-auto sm:-translate-x-1/2 z-30">
        <SearchBar />
      </div>

      {/* Layer controls — right side — z-30 */}
      <div className="absolute top-16 right-2 z-30">
        <MobileMapControls />
      </div>

      {/* Bottom controls container — z-20, stacked to prevent overlap */}
      <div className="absolute bottom-2 left-2 right-2 sm:bottom-4 z-20 pointer-events-none safe-bottom">
        <div className="flex flex-col items-center gap-2 pointer-events-auto">
          {/* Time slider */}
          <div className="w-full sm:w-96">
            <TimeSlider />
          </div>
          {/* Live counter — left-aligned on desktop */}
          <div className="w-full sm:w-auto sm:self-start">
            <LiveCounter />
          </div>
        </div>
      </div>

      {/* Welcome animation — first visit only */}
      {mounted && !hasSeenIntro && <WelcomeOverlay />}

      {/* Map tour — after animation, first visit only */}
      {mounted && hasSeenIntro && !hasSeenTour && <MapTour />}
    </div>
  );
}
