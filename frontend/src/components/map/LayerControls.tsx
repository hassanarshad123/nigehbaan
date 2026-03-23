'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { useMapStore } from '@/stores/mapStore';
import type { MapLayerId } from '@/types';
import {
  AlertTriangle,
  Factory,
  Route,
  MapPin,
  DollarSign,
  Layers,
  Search,
  MessageSquare,
  Gavel,
} from 'lucide-react';

interface LayerConfig {
  id: MapLayerId;
  label: string;
  color: string;
  icon: React.ReactNode;
}

const LAYER_CONFIGS: LayerConfig[] = [
  {
    id: 'incidents',
    label: 'Incidents',
    color: '#EF4444',
    icon: <AlertTriangle className="h-4 w-4" />,
  },
  {
    id: 'kilns',
    label: 'Brick Kilns',
    color: '#F97316',
    icon: <Factory className="h-4 w-4" />,
  },
  {
    id: 'routes',
    label: 'Trafficking Routes',
    color: '#EC4899',
    icon: <Route className="h-4 w-4" />,
  },
  {
    id: 'borders',
    label: 'Border Crossings',
    color: '#F59E0B',
    icon: <MapPin className="h-4 w-4" />,
  },
  {
    id: 'poverty',
    label: 'Poverty Index',
    color: '#06B6D4',
    icon: <DollarSign className="h-4 w-4" />,
  },
  {
    id: 'missing',
    label: 'Missing Children',
    color: '#3B82F6',
    icon: <Search className="h-4 w-4" />,
  },
  {
    id: 'reports',
    label: 'Public Reports',
    color: '#FBBF24',
    icon: <MessageSquare className="h-4 w-4" />,
  },
  {
    id: 'convictions',
    label: 'Conviction Rates',
    color: '#10B981',
    icon: <Gavel className="h-4 w-4" />,
  },
];

export function LayerControls() {
  const activeLayers = useMapStore((s) => s.activeLayers);
  const toggleLayer = useMapStore((s) => s.toggleLayer);

  return (
    <div className="rounded-lg border border-[#334155] bg-glass-surface p-3 w-full sm:w-56">
      <div className="flex items-center gap-2 mb-3 text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
        <Layers className="h-3.5 w-3.5" />
        <span>Layers</span>
      </div>

      <div className="space-y-1">
        {LAYER_CONFIGS.map((layer) => {
          const isActive = activeLayers.includes(layer.id);
          return (
            <button
              key={layer.id}
              onClick={() => toggleLayer(layer.id)}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-default',
                isActive
                  ? 'bg-[#1E293B] text-[#F8FAFC]'
                  : 'text-[#94A3B8] hover:bg-[#1E293B]/50 hover:text-[#F8FAFC]',
              )}
            >
              <div
                className={cn(
                  'flex h-5 w-5 items-center justify-center rounded',
                  isActive ? 'opacity-100' : 'opacity-40',
                )}
                style={{ color: layer.color }}
              >
                {layer.icon}
              </div>
              <span className="flex-1 text-left">{layer.label}</span>
              <div
                className={cn(
                  'h-2 w-2 rounded-full transition-default',
                  isActive ? 'opacity-100' : 'opacity-0',
                )}
                style={{ backgroundColor: layer.color }}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
