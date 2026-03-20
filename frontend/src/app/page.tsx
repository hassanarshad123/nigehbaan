'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Header } from '@/components/layout/Header';
import { LiveCounter } from '@/components/map/LiveCounter';
import { SearchBar } from '@/components/map/SearchBar';
import { IncidentTimeline } from '@/components/map/IncidentTimeline';
import { MobileMapControls } from '@/components/map/MobileMapControls';
import { TimeSlider } from '@/components/map/TimeSlider';

const MapContainer = dynamic(
  () => import('@/components/map/MapContainer').then((mod) => mod.MapContainer),
  { ssr: false },
);

export default function HomePage() {
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
      <div className="absolute bottom-2 left-2 right-2 sm:bottom-4 z-20 pointer-events-none">
        <div className="flex flex-col items-center gap-2 pointer-events-auto">
          {/* Time slider */}
          <div className="w-full sm:w-96">
            <TimeSlider />
          </div>
          {/* Incident timeline */}
          <div className="w-full sm:w-auto">
            <IncidentTimeline />
          </div>
          {/* Live counter — left-aligned on desktop */}
          <div className="w-full sm:w-auto sm:self-start">
            <LiveCounter />
          </div>
        </div>
      </div>
    </div>
  );
}
