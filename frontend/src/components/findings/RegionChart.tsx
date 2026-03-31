"use client";

import type { RegionData } from "@/lib/types";
import { severityColor } from "@/lib/constants";

/**
 * Horizontal bar chart comparing regions by event count.
 *
 * Sorted by total events descending. Bars colored by average severity.
 *
 * @param regions - Array of region data from the API.
 * @returns A styled horizontal bar chart element.
 */
export function RegionChart({ regions }: { regions: RegionData[] }) {
  if (!regions.length) return null;

  const sorted = [...regions].sort((a, b) => b.total_events - a.total_events);
  const maxEvents = sorted[0]?.total_events ?? 1;

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-sm font-medium text-text-secondary mb-3">Events by Region</h3>
      <div className="space-y-3">
        {sorted.map((region) => {
          const pct = (region.total_events / maxEvents) * 100;
          const color = severityColor(region.avg_severity);

          return (
            <div key={region.region}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-text-primary">{region.name}</span>
                <span className="font-mono-numbers text-text-muted">
                  {region.total_events.toLocaleString()}
                </span>
              </div>
              <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
              <div className="flex gap-3 mt-0.5 text-[10px] text-text-muted">
                <span>{region.spoofing_events.toLocaleString()} spoofing</span>
                <span>{region.jamming_events.toLocaleString()} jamming</span>
                <span>{region.unique_aircraft.toLocaleString()} aircraft</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
