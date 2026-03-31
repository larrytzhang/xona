"use client";

import { useState } from "react";
import { GlobeView } from "@/components/globe";
import { MOCK_ZONES } from "@/mocks/data";

/**
 * GPS Shield — Main Globe Page.
 *
 * The hero view of the app: a full-screen interactive 3D globe
 * displaying interference zones, with the Pulsar Mode toggle,
 * stats bar, region sidebar, and zone detail panel.
 *
 * Currently uses mock data. Will switch to useZonesLive() in Step 26.
 * Pulsar toggle will be added in Step 19.
 * Dashboard panels will be added in Steps 20-22.
 */
export default function Home() {
  // Pulsar toggle will be wired in Step 19.
  const [pulsarMode] = useState(false);

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <GlobeView
        zones={MOCK_ZONES}
        pulsarMode={pulsarMode}
        onZoneClick={(zone) => {
          console.log("Zone clicked:", zone.id, zone.region);
        }}
      />
    </div>
  );
}
