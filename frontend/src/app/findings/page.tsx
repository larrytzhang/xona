"use client";

import { FindingCard, TrendChart, RegionChart } from "@/components/findings";
import { MOCK_FINDINGS, MOCK_REGIONS } from "@/mocks/data";

/**
 * Key Findings page — data-driven insights from the GPS interference analysis.
 *
 * Displays 5 headline findings with animated cards, a trend chart
 * showing events over time by region, and a region comparison bar chart.
 *
 * Uses mock data. Will switch to useFindings() + useRegions() in Step 26.
 */
export default function FindingsPage() {
  const findings = MOCK_FINDINGS;
  const regions = MOCK_REGIONS;

  return (
    <div className="min-h-screen pt-20 pb-16 px-6 max-w-5xl mx-auto">
      {/* Hero */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold mb-2">Key Findings</h1>
        <p className="text-text-secondary">
          Analysis of GPS interference events detected across 7 global conflict zones,
          October 2025 — March 2026. Data source: OpenSky Network ADS-B data.
        </p>
      </div>

      {/* Finding cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        {findings.findings.map((finding, i) => (
          <FindingCard key={finding.finding_key} finding={finding} index={i} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrendChart regions={regions} />
        <RegionChart regions={regions} />
      </div>
    </div>
  );
}
