"use client";

import { X } from "lucide-react";
import type { InterferenceZone } from "@/lib/types";
import { REGION_NAMES, severityColor, severityLabel } from "@/lib/constants";

/**
 * Zone detail panel that slides in from the right when a zone is clicked.
 *
 * Displays zone header, location, duration, Pulsar comparison, and
 * affected aircraft count. Framer Motion slide animation is handled
 * via CSS transitions for simplicity.
 *
 * @param zone - The selected zone, or null to hide.
 * @param onClose - Callback to close the panel.
 * @returns The slide-in panel element, or null if no zone selected.
 */
export function ZoneDetail({
  zone,
  onClose,
}: {
  zone: InterferenceZone | null;
  onClose: () => void;
}) {
  if (!zone) return null;

  const label = severityLabel(zone.severity);
  const color = severityColor(zone.severity);
  const regionName = REGION_NAMES[zone.region] || zone.region;
  const pulsarRadius = zone.pulsar_jam_radius_km ?? zone.radius_km / 6.3;
  const reductionPct = zone.area_reduction_pct ?? 97.5;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed top-14 right-0 bottom-0 z-50 w-full md:w-[380px] glass border-l border-border-subtle overflow-y-auto animate-slide-in">
        {/* Header */}
        <div className="flex items-start justify-between p-4 border-b border-border-subtle">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span
                className="px-2 py-0.5 rounded text-xs font-medium capitalize"
                style={{ backgroundColor: color + "20", color }}
              >
                {zone.event_type}
              </span>
              <span
                className="px-2 py-0.5 rounded text-xs font-medium capitalize"
                style={{ backgroundColor: color + "20", color }}
              >
                {label}
              </span>
              {zone.is_live && (
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-accent-cyan/20 text-accent-cyan">
                  LIVE
                </span>
              )}
            </div>
            <h3 className="text-lg font-semibold">{regionName}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-bg-elevated transition-colors"
          >
            <X size={18} className="text-text-muted" />
          </button>
        </div>

        {/* Location */}
        <div className="p-4 border-b border-border-subtle">
          <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">Location</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-text-muted">Lat: </span>
              <span className="font-mono-numbers">{zone.center_lat.toFixed(2)}°</span>
            </div>
            <div>
              <span className="text-text-muted">Lon: </span>
              <span className="font-mono-numbers">{zone.center_lon.toFixed(2)}°</span>
            </div>
            <div>
              <span className="text-text-muted">Radius: </span>
              <span className="font-mono-numbers">{zone.radius_km.toFixed(0)} km</span>
            </div>
            <div>
              <span className="text-text-muted">Aircraft: </span>
              <span className="font-mono-numbers">{zone.affected_aircraft}</span>
            </div>
          </div>
        </div>

        {/* Duration */}
        <div className="p-4 border-b border-border-subtle">
          <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">Duration</h4>
          <div className="text-sm">
            <div>
              <span className="text-text-muted">Start: </span>
              <span className="font-mono-numbers">
                {new Date(zone.start_time).toLocaleString()}
              </span>
            </div>
            <div>
              <span className="text-text-muted">Status: </span>
              <span className={zone.status === "active" ? "text-severity-critical" : "text-text-secondary"}>
                {zone.status === "active" ? "Active" : "Resolved"}
              </span>
            </div>
          </div>
        </div>

        {/* Pulsar Comparison */}
        <div className="p-4">
          <h4 className="text-xs text-text-muted uppercase tracking-wider mb-3">
            Pulsar Mitigation
          </h4>

          {/* Radius comparison bars */}
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-severity-critical">GPS Radius</span>
                <span className="font-mono-numbers">{zone.radius_km.toFixed(0)} km</span>
              </div>
              <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
                <div
                  className="h-full bg-severity-critical rounded-full"
                  style={{ width: "100%" }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-accent-cyan">Pulsar Radius</span>
                <span className="font-mono-numbers">{pulsarRadius.toFixed(1)} km</span>
              </div>
              <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent-cyan rounded-full transition-all duration-500"
                  style={{ width: `${(pulsarRadius / zone.radius_km) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Spoofing elimination */}
          <div className="mt-4 p-3 rounded-lg bg-bg-elevated">
            <div className="flex items-center gap-2">
              {zone.spoofing_eliminated ? (
                <>
                  <div className="w-2 h-2 rounded-full bg-severity-low" />
                  <span className="text-sm text-severity-low font-medium">
                    Spoofing Eliminated
                  </span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full bg-text-muted" />
                  <span className="text-sm text-text-muted">
                    Jamming only — spoofing N/A
                  </span>
                </>
              )}
            </div>
            <div className="text-xs text-text-muted mt-1">
              Area reduction: <span className="font-mono-numbers text-accent-cyan">{reductionPct}%</span>
              {" · "}Signal advantage: <span className="font-mono-numbers text-accent-cyan">{zone.signal_advantage_db} dB</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
