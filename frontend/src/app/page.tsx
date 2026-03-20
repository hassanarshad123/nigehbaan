'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Header } from '@/components/layout/Header';
import { LiveCounter } from '@/components/map/LiveCounter';
import { SearchBar } from '@/components/map/SearchBar';
import { IncidentTimeline } from '@/components/map/IncidentTimeline';
import { MobileMapControls } from '@/components/map/MobileMapControls';

const MapContainer = dynamic(
  () => import('@/components/map/MapContainer').then((mod) => mod.MapContainer),
  { ssr: false },
);

export default function HomePage() {
  return (
    <div className="relative h-screen w-screen overflow-hidden">
      {/* Full-screen map */}
      <MapContainer />

      {/* Header overlay */}
      <Header />

      {/* Search bar — top center below header */}
      <div className="absolute top-16 left-2 right-14 sm:left-1/2 sm:right-auto sm:-translate-x-1/2 z-40">
        <SearchBar />
      </div>

      {/* Layer controls — right side */}
      <div className="absolute top-16 right-2 z-40">
        <MobileMapControls />
      </div>

      {/* Timeline — bottom center */}
      <div className="absolute bottom-32 left-2 right-2 sm:bottom-20 sm:left-1/2 sm:right-auto sm:-translate-x-1/2 z-40">
        <IncidentTimeline />
      </div>

      {/* Live counter — bottom left */}
      <div className="absolute bottom-2 left-2 right-2 sm:right-auto sm:left-4 sm:bottom-4 z-40">
        <LiveCounter />
      </div>
    </div>
  );
}
