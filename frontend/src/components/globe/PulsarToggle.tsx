"use client";

import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { clsx } from "clsx";

interface PulsarToggleProps {
  active: boolean;
  onToggle: () => void;
}

/**
 * GPS Mode / Pulsar Mode toggle switch — the "aha moment" control.
 *
 * Shows an attention pulse for the first ~12 seconds on load or until the
 * user interacts with it, then stops — draws the eye to the killer feature
 * without becoming annoying on repeated visits.
 */
export function PulsarToggle({ active, onToggle }: PulsarToggleProps) {
  // Attention pulse stops on first interaction or after 12s.
  const [pulsing, setPulsing] = useState(true);
  useEffect(() => {
    const t = setTimeout(() => setPulsing(false), 12_000);
    return () => clearTimeout(t);
  }, []);
  useEffect(() => {
    if (active) setPulsing(false);
  }, [active]);

  return (
    <div className="absolute top-20 right-4 z-40">
      {/* Attention halo — stops pulsing after first toggle or timeout. */}
      {pulsing && !active && (
        <span
          aria-hidden="true"
          className="absolute inset-0 rounded-xl bg-accent-cyan/10 animate-ping pointer-events-none"
        />
      )}
      <button
        onClick={() => {
          setPulsing(false);
          onToggle();
        }}
        role="switch"
        aria-checked={active}
        aria-label="Toggle Pulsar Mode"
        className={clsx(
          "relative glass rounded-xl px-4 py-3 flex items-center gap-3 transition-all duration-300",
          "hover:border-accent-cyan/40 hover:shadow-[0_0_16px_rgba(6,182,212,0.12)]",
          active && "border-accent-cyan/50 shadow-[0_0_20px_rgba(6,182,212,0.18)]"
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
              ? "97.5% area reduction • spoofing eliminated"
              : "Current GPS vulnerability"}
          </span>
        </div>
      </button>
    </div>
  );
}
