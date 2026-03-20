'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useMapStore } from '@/stores/mapStore';
import type { MapLayerId } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: Record<string, unknown>;
    properties: Record<string, unknown>;
  }>;
}

interface BorderCrossingPoint {
  id: number;
  name: string;
  borderCountry: string;
  lat: number;
  lon: number;
  vulnerabilityScore: number | null;
}

interface MapData {
  boundaries: GeoJSONFeatureCollection | null;
  incidents: GeoJSONFeatureCollection | null;
  kilns: GeoJSONFeatureCollection | null;
  borders: GeoJSONFeatureCollection | null;
  vulnerability: GeoJSONFeatureCollection | null;
  routes: GeoJSONFeatureCollection | null;
  countryMask: GeoJSONFeatureCollection | null;
  loading: boolean;
  counts: {
    incidents: number;
    kilns: number;
    borders: number;
    boundaries: number;
    vulnerability: number;
    routes: number;
  };
}

const EMPTY_FC: GeoJSONFeatureCollection = { type: 'FeatureCollection', features: [] };

function bordersToGeoJSON(points: BorderCrossingPoint[]): GeoJSONFeatureCollection {
  return {
    type: 'FeatureCollection',
    features: points.map((p) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
      properties: {
        id: p.id,
        name: p.name,
        borderCountry: p.borderCountry,
        vulnerabilityScore: p.vulnerabilityScore,
      },
    })),
  };
}

/**
 * Build a world-extent polygon with Pakistan cut out as a hole.
 * The result is a dark mask that dims everything outside Pakistan.
 */
function buildWorldMask(countryGeojson: GeoJSONFeatureCollection): GeoJSONFeatureCollection {
  // World outer ring (counter-clockwise for GeoJSON exterior)
  const worldRing: number[][] = [
    [-180, -90],
    [180, -90],
    [180, 90],
    [-180, 90],
    [-180, -90],
  ];

  // Extract all polygon rings from the country geometry to use as holes
  const holes: number[][][] = [];

  for (const feature of countryGeojson.features) {
    const geom = feature.geometry as { type: string; coordinates: unknown };
    if (geom.type === 'Polygon') {
      const coords = geom.coordinates as number[][][];
      // Each ring in the polygon becomes a hole — reverse winding
      for (const ring of coords) {
        holes.push([...ring].reverse());
      }
    } else if (geom.type === 'MultiPolygon') {
      const coords = geom.coordinates as number[][][][];
      for (const polygon of coords) {
        for (const ring of polygon) {
          holes.push([...ring].reverse());
        }
      }
    }
  }

  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [worldRing, ...holes],
        },
        properties: { name: 'world-mask' },
      },
    ],
  };
}

type LayerDataKey = 'boundaries' | 'incidents' | 'kilns' | 'borders' | 'vulnerability' | 'routes';

const LAYER_ENDPOINTS: Record<LayerDataKey, string> = {
  boundaries: '/api/v1/map/boundaries?level=2',
  incidents: '/api/v1/map/incidents',
  kilns: '/api/v1/map/kilns',
  borders: '/api/v1/map/borders',
  vulnerability: '/api/v1/map/vulnerability',
  routes: '/api/v1/map/routes',
};

const LAYER_TO_DATA: Partial<Record<MapLayerId, LayerDataKey>> = {
  incidents: 'incidents',
  kilns: 'kilns',
  borders: 'borders',
  poverty: 'vulnerability',
  routes: 'routes',
};

export function useMapData(): MapData & { filteredIncidents: GeoJSONFeatureCollection | null } {
  const activeLayers = useMapStore((s) => s.activeLayers);
  const yearRange = useMapStore((s) => s.yearRange);
  const [data, setData] = useState<Record<LayerDataKey, GeoJSONFeatureCollection | null>>({
    boundaries: null,
    incidents: null,
    kilns: null,
    borders: null,
    vulnerability: null,
    routes: null,
  });
  const [countryMask, setCountryMask] = useState<GeoJSONFeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const fetchedRef = useRef<Set<LayerDataKey>>(new Set());
  const maskFetchedRef = useRef(false);

  // Always fetch boundaries, country mask, and counter layers on mount
  useEffect(() => {
    // District boundaries (level=2)
    if (!fetchedRef.current.has('boundaries')) {
      fetchedRef.current.add('boundaries');
      fetch(`${API_BASE}${LAYER_ENDPOINTS.boundaries}`)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((raw) => {
          const geojson: GeoJSONFeatureCollection = raw?.features ? raw : EMPTY_FC;
          setData((prev) => ({ ...prev, boundaries: geojson }));
        })
        .catch((err) => console.error('Failed to fetch boundaries:', err));
    }

    // Country boundary (level=0) for mask
    if (!maskFetchedRef.current) {
      maskFetchedRef.current = true;
      fetch(`${API_BASE}/api/v1/map/boundaries?level=0`)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((raw) => {
          const geojson: GeoJSONFeatureCollection = raw?.features ? raw : EMPTY_FC;
          if (geojson.features?.length > 0) {
            setCountryMask(buildWorldMask(geojson));
          }
        })
        .catch((err) => console.error('Failed to fetch country boundary for mask:', err));
    }

    // Eager-fetch counter layers (incidents, kilns, borders) so LiveCounter
    // shows real counts without requiring the user to activate each layer.
    const counterLayers: LayerDataKey[] = ['incidents', 'kilns', 'borders'];
    for (const key of counterLayers) {
      if (fetchedRef.current.has(key)) continue;
      fetchedRef.current.add(key);
      fetch(`${API_BASE}${LAYER_ENDPOINTS[key]}`)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((raw) => {
          const geojson: GeoJSONFeatureCollection =
            key === 'borders' ? bordersToGeoJSON(raw as BorderCrossingPoint[]) : raw;
          setData((prev) => ({ ...prev, [key]: geojson?.features ? geojson : EMPTY_FC }));
        })
        .catch((err) => console.error(`Failed to fetch ${key}:`, err));
    }
  }, []);

  // Fetch layer data when activated (cached — won't re-fetch)
  useEffect(() => {
    const needed: LayerDataKey[] = [];

    for (const layerId of activeLayers) {
      const dataKey = LAYER_TO_DATA[layerId];
      if (dataKey && !fetchedRef.current.has(dataKey)) {
        needed.push(dataKey);
        fetchedRef.current.add(dataKey);
      }
    }

    if (needed.length === 0) {
      setLoading(false);
      return;
    }

    setLoading(true);

    Promise.all(
      needed.map((key) =>
        fetch(`${API_BASE}${LAYER_ENDPOINTS[key]}`)
          .then((r) => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
          })
          .then((raw) => {
            const geojson: GeoJSONFeatureCollection =
              key === 'borders' ? bordersToGeoJSON(raw as BorderCrossingPoint[]) : raw;
            if (!geojson?.features) return { key, geojson: EMPTY_FC };
            return { key, geojson };
          })
          .catch((err) => {
            console.error(`Failed to fetch ${key}:`, err);
            return { key, geojson: EMPTY_FC };
          }),
      ),
    ).then((results) => {
      setData((prev) => {
        const next = { ...prev };
        for (const { key, geojson } of results) {
          next[key] = geojson;
        }
        return next;
      });
      setLoading(false);
    });
  }, [activeLayers]);

  // Filter incidents by yearRange
  const filteredIncidents = React.useMemo(() => {
    if (!data.incidents) return null;
    const filtered = data.incidents.features.filter((f) => {
      const year = f.properties?.year as number | undefined;
      if (year == null) return true;
      return year >= yearRange[0] && year <= yearRange[1];
    });
    return { type: 'FeatureCollection' as const, features: filtered };
  }, [data.incidents, yearRange]);

  return {
    ...data,
    filteredIncidents,
    countryMask,
    loading,
    counts: {
      boundaries: data.boundaries?.features?.length ?? 0,
      incidents: filteredIncidents?.features?.length ?? 0,
      kilns: data.kilns?.features?.length ?? 0,
      borders: data.borders?.features?.length ?? 0,
      vulnerability: data.vulnerability?.features?.length ?? 0,
      routes: data.routes?.features?.length ?? 0,
    },
  };
}
