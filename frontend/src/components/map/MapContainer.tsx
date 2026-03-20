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
    'circle-color': '#EF4444',
    'circle-radius': [
      'interpolate',
      ['linear'],
      ['coalesce', ['get', 'victimCount'], 1],
      1, 4,
      5, 7,
      20, 12,
    ],
    'circle-opacity': 0.8,
    'circle-stroke-color': '#EF4444',
    'circle-stroke-width': 1,
    'circle-stroke-opacity': 0.4,
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
  const { boundaries, filteredIncidents, kilns, borders, vulnerability, routes, countryMask } = useMapData();
  const [popup, setPopup] = useState<PopupInfo | null>(null);

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

  const handleIncidentClick = useCallback((e: MapLayerMouseEvent) => {
    const feature = e.features?.[0];
    if (!feature) return;

    const coords = feature.geometry.type === 'Point'
      ? feature.geometry.coordinates as [number, number]
      : [e.lngLat.lng, e.lngLat.lat] as [number, number];

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

  return (
    <div className="absolute inset-0">
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
        onClick={handleIncidentClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        interactiveLayerIds={['incidents-circle']}
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
      </Map>
    </div>
  );
}
