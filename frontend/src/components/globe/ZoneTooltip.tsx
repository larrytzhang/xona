"use client";

import type { InterferenceZone } from "@/lib/types";
import { REGION_NAMES, severityColor, severityLabel } from "@/lib/constants";

/**
 * Tooltip displayed when hovering over an interference zone on the globe.
 *
 * Shows a glass card with zone type, severity, region, and aircraft count.
 * Positioned near the cursor via absolute positioning.
 *
 * @param zone - The interference zone being hovered, or null to hide.
 * @param x - Screen X coordinate for positioning.
 * @param y - Screen Y coordinate for positioning.
 * @returns The tooltip element, or null if no zone is hovered.
 */
export function ZoneTooltip({
  zone,
  x,
  y,
}: {
  zone: InterferenceZone | null;
  x: number;
  y: number;
}) {
  if (!zone) return null;

  const label = severityLabel(zone.severity);
  const color = severityColor(zone.severity);
  const regionName = REGION_NAMES[zone.region] || zone.region;

  return (
    <div
      className="absolute z-50 pointer-events-none glass rounded-lg px-3 py-2 text-sm min-w-[180px]"
      style={{ left: x + 12, top: y + 12 }}
    >
      <div className="flex items-center gap-2 mb-1">
        <div
          className="w-2.5 h-2.5 rounded-full"
          style={{ backgroundColor: color }}
        />
        <span className="font-medium capitalize">{zone.event_type}</span>
        {zone.is_live && (
          <span className="text-xs text-severity-low animate-pulse">LIVE</span>
        )}
      </div>

      <div className="text-text-secondary text-xs space-y-0.5">
        <div>{regionName}</div>
        <div>
          Severity:{" "}
          <span className="capitalize" style={{ color }}>
            {label}
          </span>{" "}
          <span className="font-mono-numbers">({zone.severity})</span>
        </div>
        <div>{zone.affected_aircraft} aircraft affected</div>
        <div className="font-mono-numbers">{zone.radius_km.toFixed(0)} km radius</div>
      </div>
    </div>
  );
}
