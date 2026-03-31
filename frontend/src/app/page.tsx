"use client";

import { useState } from "react";
import { GlobeView, PulsarToggle } from "@/components/globe";
import { StatsBar, ZoneDetail, RegionList } from "@/components/dashboard";
import { MOCK_ZONES, MOCK_STATS, MOCK_REGIONS } from "@/mocks/data";
import type { InterferenceZone } from "@/lib/types";

/**
 * GPS Shield — Main Globe Page.
 *
 * The hero view: full-screen 3D globe with interference zones,
 * Pulsar Mode toggle, stats bar, region sidebar, and zone detail panel.
 *
 * Currently uses mock data. Will switch to real API hooks in Step 26.
 */
export default function Home() {
  const [pulsarMode, setPulsarMode] = useState(false);
  const [selectedZone, setSelectedZone] = useState<InterferenceZone | null>(null);
  const [flyTo, setFlyTo] = useState<{
    latitude: number;
    longitude: number;
    zoom: number;
  } | null>(null);

  const handleZoneClick = (zone: InterferenceZone) => {
    setSelectedZone(zone);
    setFlyTo({
      latitude: zone.center_lat,
      longitude: zone.center_lon,
      zoom: 4.5,
    });
  };

  const handleRegionClick = (target: {
    latitude: number;
    longitude: number;
    zoom: number;
  }) => {
    setFlyTo(target);
  };

  const handleCloseDetail = () => {
    setSelectedZone(null);
    setFlyTo(null);
  };

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Globe */}
      <GlobeView
        zones={MOCK_ZONES}
        pulsarMode={pulsarMode}
        onZoneClick={handleZoneClick}
        flyTo={flyTo}
      />

      {/* Stats bar */}
      <StatsBar stats={MOCK_STATS} />

      {/* Region sidebar */}
      <RegionList
        regions={MOCK_REGIONS}
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
