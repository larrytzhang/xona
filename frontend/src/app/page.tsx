"use client";

import { useState } from "react";
import { GlobeView, PulsarToggle } from "@/components/globe";
import { MOCK_ZONES } from "@/mocks/data";

/**
 * GPS Shield — Main Globe Page.
 *
 * The hero view of the app: a full-screen interactive 3D globe
 * displaying interference zones with the Pulsar Mode toggle.
 *
 * The Pulsar toggle is THE feature — clicking it triggers a smooth
 * 1.5s animation where zone radii shrink 97%, colors shift to cyan,
 * and "spoofing eliminated" labels appear.
 *
 * Dashboard panels (stats bar, region list, zone detail) will be
 * added in Steps 20-22.
 */
export default function Home() {
  const [pulsarMode, setPulsarMode] = useState(false);

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <GlobeView
        zones={MOCK_ZONES}
        pulsarMode={pulsarMode}
        onZoneClick={(zone) => {
          console.log("Zone clicked:", zone.id, zone.region);
        }}
      />
      <PulsarToggle
        active={pulsarMode}
        onToggle={() => setPulsarMode((prev) => !prev)}
      />
    </div>
  );
}
