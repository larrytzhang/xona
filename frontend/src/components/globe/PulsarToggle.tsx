"use client";

import { Shield } from "lucide-react";
import { clsx } from "clsx";

/**
 * Props for the PulsarToggle component.
 *
 * @param active - Whether Pulsar Mode is currently active.
 * @param onToggle - Callback when the toggle is clicked.
 */
interface PulsarToggleProps {
  active: boolean;
  onToggle: () => void;
}

/**
 * GPS Mode / Pulsar Mode toggle switch.
 *
 * Positioned in the top-right corner of the globe view. This is
 * THE key feature of the app — the visual "aha" moment for executives.
 *
 * GPS Mode (default): Shows full interference radii, red/orange zones.
 * Pulsar Mode: Zones shrink 97%, shift to cyan, "spoofing eliminated" labels.
 *
 * The toggle itself is a glass panel with a prominent switch and
 * clear labeling of both modes.
 *
 * @param props - PulsarToggleProps
 * @returns The toggle component positioned absolutely in the top-right.
 */
export function PulsarToggle({ active, onToggle }: PulsarToggleProps) {
  return (
    <div className="absolute top-20 right-4 z-40">
      <button
        onClick={onToggle}
        className={clsx(
          "glass rounded-xl px-4 py-3 flex items-center gap-3 transition-all duration-300",
          "hover:border-accent-cyan/30",
          active && "border-accent-cyan/50 shadow-[0_0_20px_rgba(6,182,212,0.15)]"
        )}
      >
        {/* Toggle track */}
        <div
          className={clsx(
            "relative w-12 h-6 rounded-full transition-colors duration-300",
            active ? "bg-accent-cyan/30" : "bg-bg-elevated"
          )}
        >
          {/* Toggle thumb */}
          <div
            className={clsx(
              "absolute top-0.5 w-5 h-5 rounded-full transition-all duration-300 shadow-md",
              active
                ? "left-[26px] bg-accent-cyan"
                : "left-0.5 bg-text-secondary"
            )}
          />
        </div>

        {/* Labels */}
        <div className="flex flex-col items-start">
          <div className="flex items-center gap-1.5">
            <Shield
              size={14}
              className={clsx(
                "transition-colors duration-300",
                active ? "text-accent-cyan" : "text-text-muted"
              )}
            />
            <span
              className={clsx(
                "text-sm font-medium transition-colors duration-300",
                active ? "text-accent-cyan" : "text-text-primary"
              )}
            >
              {active ? "Pulsar Mode" : "GPS Mode"}
            </span>
          </div>
          <span className="text-[10px] text-text-muted leading-tight">
            {active
              ? "97% area reduction • spoofing eliminated"
              : "Current GPS vulnerability"}
          </span>
        </div>
      </button>
    </div>
  );
}
