'use client';

import React, { useCallback, useRef } from 'react';
import Map, { Marker, NavigationControl, type MapLayerMouseEvent } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

interface LocationPickerProps {
  latitude: number | null;
  longitude: number | null;
  onClick: (lat: number, lon: number) => void;
}

export function LocationPicker({ latitude, longitude, onClick }: LocationPickerProps) {
  const mapRef = useRef<maplibregl.Map | null>(null);

  const handleClick = useCallback(
    (e: MapLayerMouseEvent) => {
      onClick(e.lngLat.lat, e.lngLat.lng);
    },
    [onClick],
  );

  return (
    <div className="rounded-lg border border-[#334155] overflow-hidden h-64">
      <Map
        ref={(ref) => {
          if (ref) mapRef.current = ref.getMap();
        }}
        mapStyle={DARK_STYLE}
        initialViewState={{
          latitude: latitude ?? 30.3753,
          longitude: longitude ?? 69.3451,
          zoom: latitude != null ? 10 : 5,
        }}
        style={{ width: '100%', height: '100%' }}
        onClick={handleClick}
        cursor="crosshair"
        attributionControl={true}
        maxZoom={18}
        minZoom={3}
      >
        <NavigationControl position="top-right" showCompass={false} />

        {latitude != null && longitude != null && (
          <Marker latitude={latitude} longitude={longitude} anchor="bottom">
            <div className="flex flex-col items-center">
              <div className="h-6 w-6 rounded-full bg-[#EF4444] border-2 border-white shadow-lg marker-pulse" />
              <div className="h-2 w-0.5 bg-[#EF4444]" />
            </div>
          </Marker>
        )}
      </Map>
    </div>
  );
}
