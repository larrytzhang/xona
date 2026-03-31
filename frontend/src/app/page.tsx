"use client";

import { GlobeView } from "@/components/globe";

/**
 * GPS Shield — Main Globe Page.
 *
 * The hero view of the app: a full-screen interactive 3D globe
 * displaying interference zones, with the Pulsar Mode toggle,
 * stats bar, region sidebar, and zone detail panel.
 *
 * Currently renders the base globe (Step 17).
 * Data layers added in Step 18, Pulsar toggle in Step 19,
 * dashboard panels in Steps 20-22.
 */
export default function Home() {
  return (
    <div className="relative w-full h-screen overflow-hidden">
      <GlobeView />
    </div>
  );
}
