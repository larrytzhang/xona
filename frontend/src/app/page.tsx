"use client";

import { useState, useCallback } from "react";
import { GlobeView, PulsarToggle } from "@/components/globe";
import { StatsBar, ZoneDetail, RegionList } from "@/components/dashboard";
import { useZonesLive, useStats, useRegions } from "@/lib/hooks";
import type { InterferenceZone } from "@/lib/types";

/**
 * GPS Shield — Main Globe Page.
 *
 * The hero view: full-screen 3D globe with interference zones,
 * Pulsar Mode toggle, stats bar, region sidebar, and zone detail panel.
 *
 * Fetches live zone data, global stats, and region breakdowns from the
 * backend API via React Query hooks. Shows loading/error/empty states
 * when the backend is unreachable or has no data.
 */
export default function Home() {
  const [pulsarMode, setPulsarMode] = useState(false);
  const [selectedZone, setSelectedZone] = useState<InterferenceZone | null>(null);
  const [flyTo, setFlyTo] = useState<{
    latitude: number;
    longitude: number;
    zoom: number;
  } | null>(null);

  const zonesQuery = useZonesLive();
  const statsQuery = useStats();
  const regionsQuery = useRegions();

  const zones = zonesQuery.data?.zones ?? [];
  const stats = statsQuery.data ?? null;
  const regions = regionsQuery.data?.regions ?? [];

  /** Select a zone and fly the camera to it. */
  const handleZoneClick = useCallback((zone: InterferenceZone) => {
    setSelectedZone(zone);
    setFlyTo({
      latitude: zone.center_lat,
      longitude: zone.center_lon,
      zoom: 4.5,
    });
  }, []);

  /** Fly the camera to a region's center coordinates. */
  const handleRegionClick = useCallback((target: {
    latitude: number;
    longitude: number;
    zoom: number;
  }) => {
    setFlyTo(target);
  }, []);

  /** Close the zone detail panel and reset camera. */
  const handleCloseDetail = useCallback(() => {
    setSelectedZone(null);
    setFlyTo(null);
  }, []);

  /** Retry all failed queries. */
  const handleRetry = () => {
    zonesQuery.refetch();
    statsQuery.refetch();
    regionsQuery.refetch();
  };

  const isError = zonesQuery.isError || statsQuery.isError;

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Globe — always render, shows empty globe while loading */}
      <GlobeView
        zones={zones}
        pulsarMode={pulsarMode}
        onZoneClick={handleZoneClick}
        flyTo={flyTo}
      />

      {/* Connection error overlay */}
      {isError && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="glass rounded-xl p-6 max-w-sm text-center">
            <p className="text-text-primary font-medium mb-2">Could not connect to backend</p>
            <p className="text-text-muted text-sm mb-4">
              The API server may be starting up. Check that the backend is running.
            </p>
            <button
              onClick={handleRetry}
              className="px-4 py-2 rounded-lg bg-accent-cyan/20 text-accent-cyan text-sm font-medium hover:bg-accent-cyan/30 transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}

      {/* Globe loading spinner — shown while zones are loading for the first time */}
      {zonesQuery.isLoading && (
        <div className="absolute inset-0 z-40 flex items-center justify-center pointer-events-none">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-accent-cyan/30 border-t-accent-cyan rounded-full animate-spin" />
            <span className="text-text-muted text-sm">Loading zone data...</span>
          </div>
        </div>
      )}

      {/* Empty state — backend reachable but no zones detected */}
      {!zonesQuery.isLoading && !zonesQuery.isError && zones.length === 0 && (
        <div className="absolute inset-0 z-40 flex items-center justify-center pointer-events-none">
          <div className="glass rounded-xl p-6 max-w-sm text-center pointer-events-auto">
            <p className="text-text-primary font-medium mb-1">No active interference zones</p>
            <p className="text-text-muted text-sm">
              No GPS anomalies detected in the last 24 hours. Historical data may not be loaded yet.
            </p>
          </div>
        </div>
      )}

      {/* Stats bar */}
      <StatsBar stats={stats} />

      {/* Region sidebar */}
      <RegionList
        regions={regions}
        activeRegion={selectedZone?.region ?? null}
        onRegionClick={handleRegionClick}
      />

      {/* Pulsar toggle */}
      <PulsarToggle
        active={pulsarMode}
        onToggle={() => setPulsarMode((prev) => !prev)}
      />

      {/* Zone detail panel */}
      <ZoneDetail zone={selectedZone} onClose={handleCloseDetail} />
    </div>
  );
}
