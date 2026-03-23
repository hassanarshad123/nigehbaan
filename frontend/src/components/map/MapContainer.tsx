'use client';

import React, { useCallback, useRef, useState } from 'react';
import Map, {
  NavigationControl,
  ScaleControl,
  Source,
  Layer,
  Popup,
  type ViewStateChangeEvent,
  type LayerProps,
  type MapLayerMouseEvent,
} from 'react-map-gl/maplibre';
import { useMapStore } from '@/stores/mapStore';
import { useMapData } from '@/hooks/useMapData';
import { IncidentPopup } from './IncidentPopup';
import { DistrictPopup } from './DistrictPopup';
import { buildIncidentColorExpression } from '@/lib/incidentColors';
import 'maplibre-gl/dist/maplibre-gl.css';

const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

const worldMaskLayer: LayerProps = {
  id: 'world-mask',
  type: 'fill',
  paint: {
    'fill-color': '#000000',
    'fill-opacity': 0.6,
  },
};

const boundaryFillLayer: LayerProps = {
  id: 'boundaries-fill',
  type: 'fill',
  paint: {
    'fill-color': '#06B6D4',
    'fill-opacity': 0.05,
  },
};

const boundaryLineLayer: LayerProps = {
  id: 'boundaries-line',
  type: 'line',
  paint: {
    'line-color': '#06B6D4',
    'line-width': 1,
    'line-opacity': 0.6,
  },
};

const incidentLayer: LayerProps = {
  id: 'incidents-circle',
  type: 'circle',
  paint: {
    'circle-color': buildIncidentColorExpression() as never,
    'circle-radius': [
      'interpolate',
      ['linear'],
      ['coalesce', ['get', 'victimCount'], 1],
      1, 4,
      5, 7,
      20, 12,
    ],
    'circle-opacity': 0.8,
    'circle-stroke-color': buildIncidentColorExpression() as never,
    'circle-stroke-width': 1,
    'circle-stroke-opacity': 0.4,
  },
};

const missingLayer: LayerProps = {
  id: 'missing-circle',
  type: 'circle',
  paint: {
    'circle-color': '#3B82F6',
    'circle-radius': 6,
    'circle-opacity': 0.9,
    'circle-stroke-color': '#FFFFFF',
    'circle-stroke-width': 1.5,
    'circle-stroke-opacity': 0.8,
  },
};

const reportsLayer: LayerProps = {
  id: 'reports-circle',
  type: 'circle',
  paint: {
    'circle-color': '#FBBF24',
    'circle-radius': 5,
    'circle-opacity': 0.9,
    'circle-stroke-color': '#FFFFFF',
    'circle-stroke-width': 1,
    'circle-stroke-opacity': 0.7,
  },
};

const convictionFillLayer: LayerProps = {
  id: 'convictions-fill',
  type: 'fill',
  paint: {
    'fill-color': [
      'interpolate',
      ['linear'],
      ['coalesce', ['get', 'convictionRate'], 0],
      0, '#EF4444',
      0.3, '#F97316',
      0.5, '#FBBF24',
      0.7, '#10B981',
      1.0, '#065F46',
    ],
    'fill-opacity': 0.4,
  },
};

const convictionLineLayer: LayerProps = {
  id: 'convictions-line',
  type: 'line',
  paint: {
    'line-color': '#10B981',
    'line-width': 0.5,
    'line-opacity': 0.6,
  },
};

const kilnLayer: LayerProps = {
  id: 'kilns-circle',
  type: 'circle',
  paint: {
    'circle-color': '#F97316',
    'circle-radius': 3,
    'circle-opacity': 0.6,
    'circle-stroke-color': '#F97316',
    'circle-stroke-width': 0.5,
    'circle-stroke-opacity': 0.3,
  },
};

const borderLayer: LayerProps = {
  id: 'borders-circle',
  type: 'circle',
  paint: {
    'circle-color': '#F59E0B',
    'circle-radius': 7,
    'circle-opacity': 0.9,
    'circle-stroke-color': '#FFFFFF',
    'circle-stroke-width': 2,
    'circle-stroke-opacity': 0.8,
  },
};

const vulnerabilityFillLayer: LayerProps = {
  id: 'vulnerability-fill',
  type: 'fill',
  paint: {
    'fill-color': [
      'interpolate',
      ['linear'],
      ['coalesce', ['get', 'traffickingRiskScore'], 0],
      0, '#10B981',     // green — low risk
      0.25, '#84CC16',  // lime
      0.4, '#FBBF24',   // yellow
      0.55, '#F97316',  // orange
      0.7, '#EF4444',   // red — high risk
      1.0, '#991B1B',   // dark red — extreme risk
    ],
    'fill-opacity': 0.4,
  },
};

const vulnerabilityLineLayer: LayerProps = {
  id: 'vulnerability-line',
  type: 'line',
  paint: {
    'line-color': '#FBBF24',
    'line-width': 0.5,
    'line-opacity': 0.6,
  },
};

const routesLineLayer: LayerProps = {
  id: 'routes-line',
  type: 'line',
  paint: {
    'line-color': '#EC4899',
    'line-width': 2,
    'line-dasharray': [4, 2],
    'line-opacity': 0.8,
  },
};

interface PopupInfo {
  latitude: number;
  longitude: number;
  properties: Record<string, unknown>;
}

export function MapContainer() {
  const viewport = useMapStore((s) => s.viewport);
  const setViewport = useMapStore((s) => s.setViewport);
  const activeLayers = useMapStore((s) => s.activeLayers);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const { boundaries, filteredIncidents, missingChildren, kilns, borders, vulnerability, routes, reports, convictions, countryMask, loading, errors } = useMapData();
  const [popup, setPopup] = useState<PopupInfo | null>(null);
  const [districtPopup, setDistrictPopup] = useState<{ pcode: string; latitude: number; longitude: number } | null>(null);
  const [districtData, setDistrictData] = useState<Record<string, unknown> | null>(null);
  const [errorDismissed, setErrorDismissed] = useState(false);

  const handleMove = useCallback(
    (evt: ViewStateChangeEvent) => {
      setViewport({
        latitude: evt.viewState.latitude,
        longitude: evt.viewState.longitude,
        zoom: evt.viewState.zoom,
      });
    },
    [setViewport],
  );

  const handleMapClick = useCallback((e: MapLayerMouseEvent) => {
    const feature = e.features?.[0];
    if (!feature) return;

    const layerId = (feature.layer as { id?: string })?.id ?? '';

    if (layerId === 'boundaries-fill') {
      const pcode = String(feature.properties?.pcode ?? '');
      if (!pcode) return;
      setPopup(null);
      setDistrictPopup({ pcode, latitude: e.lngLat.lat, longitude: e.lngLat.lng });
      setDistrictData(null);
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? '';
      fetch(`${apiBase}/api/v1/map/district-summary/${pcode}`)
        .then((r) => r.ok ? r.json() : null)
        .then((data) => { if (data) setDistrictData(data); })
        .catch(() => {});
      return;
    }

    // Incident or other point layer click
    const coords = feature.geometry.type === 'Point'
      ? feature.geometry.coordinates as [number, number]
      : [e.lngLat.lng, e.lngLat.lat] as [number, number];

    setDistrictPopup(null);
    setPopup({
      longitude: coords[0],
      latitude: coords[1],
      properties: (feature.properties ?? {}) as Record<string, unknown>,
    });
  }, []);

  const handleMouseEnter = useCallback(() => {
    const map = mapRef.current;
    if (map) map.getCanvas().style.cursor = 'pointer';
  }, []);

  const handleMouseLeave = useCallback(() => {
    const map = mapRef.current;
    if (map) map.getCanvas().style.cursor = '';
  }, []);

  const vis = (layerId: string): 'visible' | 'none' =>
    activeLayers.includes(layerId as never) ? 'visible' : 'none';

  const errorKeys = Object.keys(errors);

  return (
    <div className="absolute inset-0" data-tour-step="incidents">
      {/* Map layer error banner */}
      {errorKeys.length > 0 && !errorDismissed && (
        <div className="absolute top-14 left-2 right-2 sm:left-auto sm:right-4 sm:w-72 z-40">
          <div className="rounded-lg border border-[#EF4444]/30 bg-[#1E293B]/95 backdrop-blur-sm px-3 py-2 shadow-xl">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-[#EF4444]">Failed to load layers</p>
              <button
                onClick={() => setErrorDismissed(true)}
                className="text-[#94A3B8] hover:text-[#F8FAFC] text-xs"
                aria-label="Dismiss error"
              >
                ✕
              </button>
            </div>
            <div className="space-y-0.5">
              {errorKeys.map((key) => (
                <p key={key} className="text-xs text-[#94A3B8]">
                  {key}: connection failed
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay — shown while fetching initial map data */}
      {loading && !boundaries && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#0F172A]/80 backdrop-blur-sm transition-opacity duration-500">
          <div className="flex flex-col items-center gap-3">
            <div className="h-10 w-10 rounded-full border-2 border-[#06B6D4]/30 border-t-[#06B6D4] animate-spin" />
            <p className="text-sm text-[#94A3B8]">Loading map data...</p>
          </div>
        </div>
      )}

      <Map
        ref={(ref) => {
          if (ref) {
            mapRef.current = ref.getMap();
          }
        }}
        mapStyle={DARK_STYLE}
        latitude={viewport.latitude}
        longitude={viewport.longitude}
        zoom={viewport.zoom}
        onMove={handleMove}
        onClick={handleMapClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        interactiveLayerIds={['incidents-circle', 'missing-circle', 'reports-circle', 'boundaries-fill']}
        style={{ width: '100%', height: '100%' }}
        attributionControl={true}
        maxZoom={18}
        minZoom={3}
      >
        <NavigationControl position="bottom-right" showCompass={false} />
        <ScaleControl position="bottom-right" />

        {/* Dark mask — dims everything outside Pakistan */}
        {countryMask && (
          <Source id="world-mask" type="geojson" data={countryMask}>
            <Layer {...worldMaskLayer} />
          </Source>
        )}

        {/* District boundaries — always visible */}
        {boundaries && (
          <Source id="boundaries" type="geojson" data={boundaries}>
            <Layer {...boundaryFillLayer} />
            <Layer {...boundaryLineLayer} />
          </Source>
        )}

        {/* Vulnerability choropleth — rendered before point layers so points appear on top */}
        {vulnerability && (
          <Source id="vulnerability" type="geojson" data={vulnerability}>
            <Layer
              {...vulnerabilityFillLayer}
              layout={{ visibility: vis('poverty') }}
            />
            <Layer
              {...vulnerabilityLineLayer}
              layout={{ visibility: vis('poverty') }}
            />
          </Source>
        )}

        {/* Trafficking routes */}
        {routes && (
          <Source id="routes" type="geojson" data={routes}>
            <Layer
              {...routesLineLayer}
              layout={{ visibility: vis('routes') }}
            />
          </Source>
        )}

        {/* Incidents */}
        {filteredIncidents && (
          <Source id="incidents" type="geojson" data={filteredIncidents}>
            <Layer
              {...incidentLayer}
              layout={{ visibility: vis('incidents') }}
            />
          </Source>
        )}

        {/* Brick kilns */}
        {kilns && (
          <Source id="kilns" type="geojson" data={kilns}>
            <Layer
              {...kilnLayer}
              layout={{ visibility: vis('kilns') }}
            />
          </Source>
        )}

        {/* Border crossings */}
        {borders && (
          <Source id="borders" type="geojson" data={borders}>
            <Layer
              {...borderLayer}
              layout={{ visibility: vis('borders') }}
            />
          </Source>
        )}

        {/* Conviction rates choropleth */}
        {convictions && (
          <Source id="convictions" type="geojson" data={convictions}>
            <Layer
              {...convictionFillLayer}
              layout={{ visibility: vis('convictions') }}
            />
            <Layer
              {...convictionLineLayer}
              layout={{ visibility: vis('convictions') }}
            />
          </Source>
        )}

        {/* Missing children */}
        {missingChildren && (
          <Source id="missing" type="geojson" data={missingChildren}>
            <Layer
              {...missingLayer}
              layout={{ visibility: vis('missing') }}
            />
          </Source>
        )}

        {/* Public reports */}
        {reports && (
          <Source id="reports" type="geojson" data={reports}>
            <Layer
              {...reportsLayer}
              layout={{ visibility: vis('reports') }}
            />
          </Source>
        )}

        {/* Incident detail popup */}
        {popup && (
          <Popup
            latitude={popup.latitude}
            longitude={popup.longitude}
            onClose={() => setPopup(null)}
            closeButton={false}
            closeOnClick={false}
            anchor="bottom"
            offset={12}
            className="[&>.maplibregl-popup-content]:!bg-transparent [&>.maplibregl-popup-content]:!p-0 [&>.maplibregl-popup-content]:!shadow-none [&>.maplibregl-popup-tip]:!border-t-[#1E293B]"
          >
            <IncidentPopup
              properties={popup.properties}
              onClose={() => setPopup(null)}
            />
          </Popup>
        )}

        {/* District summary popup */}
        {districtPopup && (
          <Popup
            latitude={districtPopup.latitude}
            longitude={districtPopup.longitude}
            onClose={() => setDistrictPopup(null)}
            closeButton={false}
            closeOnClick={false}
            anchor="bottom"
            offset={12}
            className="[&>.maplibregl-popup-content]:!bg-transparent [&>.maplibregl-popup-content]:!p-0 [&>.maplibregl-popup-content]:!shadow-none [&>.maplibregl-popup-tip]:!border-t-[#1E293B]"
          >
            <DistrictPopup
              pcode={districtPopup.pcode}
              data={districtData}
              onClose={() => setDistrictPopup(null)}
            />
          </Popup>
        )}
      </Map>
    </div>
  );
}
