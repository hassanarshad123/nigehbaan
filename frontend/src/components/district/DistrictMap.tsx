'use client';

import React from 'react';
import Map, { NavigationControl } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

interface DistrictMapProps {
  latitude: number;
  longitude: number;
  zoom?: number;
}

export function DistrictMap({
  latitude,
  longitude,
  zoom = 9,
}: DistrictMapProps) {
  return (
    <div className="h-64 rounded-lg border border-[#334155] overflow-hidden">
      <Map
        mapStyle={DARK_STYLE}
        initialViewState={{
          latitude,
          longitude,
          zoom,
        }}
        style={{ width: '100%', height: '100%' }}
        attributionControl={false}
        interactive={false}
      >
        <NavigationControl position="top-right" showCompass={false} />
      </Map>
    </div>
  );
}
