"use client";

import { clsx } from "clsx";
import type { RegionData } from "@/lib/types";
import { severityColor } from "@/lib/constants";
import { REGION_CENTERS } from "@/lib/constants";

/**
 * Region sidebar listing all interference regions.
 *
 * Each region shows name, event count, severity indicator, and
 * a tiny sparkline of recent trend. Clicking a region flies the
 * globe camera to that region's center.
 *
 * @param regions - Array of region data from the API.
 * @param activeRegion - Currently selected region ID, or null.
 * @param onRegionClick - Callback with region's camera target.
 * @returns The collapsible left sidebar element.
 */
export function RegionList({
  regions,
  activeRegion,
  onRegionClick,
}: {
  regions: RegionData[];
  activeRegion: string | null;
  onRegionClick: (target: { latitude: number; longitude: number; zoom: number }) => void;
}) {
  if (!regions.length) return null;

  return (
    <div className="hidden md:block absolute top-[7.5rem] left-4 z-30 glass rounded-xl w-56 max-h-[calc(100vh-10rem)] overflow-y-auto">
      <div className="p-3 border-b border-border-subtle">
        <h3 className="text-xs text-text-muted uppercase tracking-wider font-medium">Regions</h3>
      </div>

      <div className="py-1">
        {regions.map((region) => {
          const isActive = region.region === activeRegion;
          const center = REGION_CENTERS[region.region];
          const color = severityColor(region.avg_severity);

          return (
            <button
              key={region.region}
              onClick={() => center && onRegionClick(center)}
              className={clsx(
                "w-full px-3 py-2 text-left flex items-center gap-2 transition-colors",
                "hover:bg-bg-elevated",
                isActive && "bg-accent-cyan/10"
              )}
            >
              {/* Severity dot */}
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />

              <div className="flex-1 min-w-0">
                <div className="text-sm truncate">{region.name}</div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono-numbers text-text-muted">
                    {region.total_events.toLocaleString()} events
                  </span>
                  {/* Sparkline */}
                  {region.trend.length > 0 && (
                    <Sparkline data={region.trend.map((t) => t.events)} />
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Tiny inline sparkline chart for trend visualization.
 *
 * @param data - Array of numeric values to plot.
 * @returns A small SVG sparkline.
 */
function Sparkline({ data }: { data: number[] }) {
  if (data.length < 2) return null;

  const width = 40;
  const height = 12;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} className="flex-shrink-0">
      <polyline
        points={points}
        fill="none"
        stroke="#06B6D4"
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
