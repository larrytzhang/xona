"use client";

import { useEffect, useRef, useState } from "react";
import { Info } from "lucide-react";
import { LivePulse } from "@/components/globe";
import type { StatsResponse } from "@/lib/types";

/**
 * Animate a number counting up from the previous value to the new target.
 *
 * On first render animates from 0. On subsequent target changes, animates
 * from the old value to the new one — avoids jarring resets to zero.
 *
 * @param target - The final number to reach.
 * @param duration - Animation duration in milliseconds.
 * @returns The current animated value.
 */
function useCountUp(target: number, duration = 1500): number {
  const [value, setValue] = useState(0);
  const prevTarget = useRef(0);
  const startTime = useRef<number | null>(null);
  const rafId = useRef<number | null>(null);

  useEffect(() => {
    const from = prevTarget.current;
    prevTarget.current = target;
    startTime.current = null;

    const animate = (timestamp: number) => {
      if (startTime.current === null) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(from + eased * (target - from)));
      if (progress < 1) {
        rafId.current = requestAnimationFrame(animate);
      }
    };

    rafId.current = requestAnimationFrame(animate);
    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, [target, duration]);

  return value;
}

/**
 * Data transparency badge — tells reviewers the data is synthetic.
 *
 * Hover reveals a tooltip with methodology context. This is deliberately
 * visible at all times so no reviewer comes away thinking the numbers
 * were fabricated.
 */
function DataSourceBadge() {
  return (
    <div className="relative group hidden md:block">
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-bg-elevated border border-border-subtle text-[11px] text-text-secondary">
        <Info size={12} className="text-accent-cyan" />
        <span>Synthetic demo data</span>
      </div>
      <div
        role="tooltip"
        className="absolute right-0 top-full mt-2 w-64 p-3 rounded-lg glass text-[11px] text-text-secondary leading-relaxed opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-[60]"
      >
        Calibrated to published GPS interference reports from C4ADS and
        EUROCONTROL. The detection pipeline is real — the same code runs on
        live OpenSky Network data when enabled.
      </div>
    </div>
  );
}

/** Format an ISO-ish date string as "Oct 2025". Falls back to the raw value. */
function formatDate(raw: string): string {
  try {
    const d = new Date(raw);
    if (Number.isNaN(d.valueOf())) return raw;
    return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  } catch {
    return raw;
  }
}

function StatCard({ label, value, suffix = "" }: { label: string; value: number; suffix?: string }) {
  const animated = useCountUp(value);
  return (
    <div className="flex flex-col items-center px-4">
      <span className="font-mono-numbers text-lg font-semibold text-text-primary">
        {animated.toLocaleString()}{suffix}
      </span>
      <span className="text-[10px] text-text-muted uppercase tracking-wider">{label}</span>
    </div>
  );
}

/**
 * Top stats bar displaying key dashboard metrics.
 *
 * Fixed below the nav, shows 4 stat cards with count-up animation
 * and a live polling status indicator.
 *
 * @param stats - Global stats from the API, or null if loading.
 * @returns The stats bar element.
 */
export function StatsBar({ stats }: { stats: StatsResponse | null }) {
  if (!stats) {
    return (
      <div className="absolute top-14 left-0 right-0 z-30 glass h-16 flex items-center justify-center">
        <span className="text-text-muted text-sm">Loading statistics...</span>
      </div>
    );
  }

  return (
    <div className="absolute top-14 left-0 right-0 z-30 glass h-16 flex items-center justify-between px-4 md:px-6 border-b border-border-subtle">
      <div className="flex items-center gap-1 md:gap-2 divide-x divide-border-subtle overflow-x-auto">
        <StatCard label="Events Detected" value={stats.total_events} />
        <StatCard label="Active Zones" value={stats.live.active_zones} />
        <StatCard label="Aircraft Affected" value={stats.total_aircraft_affected} />
        <div className="hidden md:flex flex-col items-center px-4">
          <span className="text-xs font-mono-numbers text-text-primary">
            {formatDate(stats.date_range.start)} — {formatDate(stats.date_range.end)}
          </span>
          <span className="text-[10px] text-text-muted uppercase tracking-wider">Analysis Period</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <DataSourceBadge />
        <LivePulse
          status={stats.live.poll_status}
          lastPoll={stats.live.last_poll}
        />
      </div>
    </div>
  );
}
