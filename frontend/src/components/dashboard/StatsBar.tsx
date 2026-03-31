"use client";

import { useEffect, useRef, useState } from "react";
import { LivePulse } from "@/components/globe/LivePulse";
import type { StatsResponse } from "@/lib/types";

/**
 * Animate a number counting up from 0 to target over duration ms.
 *
 * @param target - The final number to reach.
 * @param duration - Animation duration in milliseconds.
 * @returns The current animated value.
 */
function useCountUp(target: number, duration = 1500): number {
  const [value, setValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const rafId = useRef<number | null>(null);

  useEffect(() => {
    startTime.current = null;

    const animate = (timestamp: number) => {
      if (startTime.current === null) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setValue(Math.round(eased * target));
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
 * A single stat card in the stats bar.
 *
 * @param label - Stat label text.
 * @param value - Numeric value (animated count-up).
 * @param suffix - Optional suffix (e.g., "%").
 * @returns Styled stat card element.
 */
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
    <div className="absolute top-14 left-0 right-0 z-30 glass h-16 flex items-center justify-between px-6 border-b border-border-subtle">
      <div className="flex items-center gap-2 divide-x divide-border-subtle">
        <StatCard label="Events Detected" value={stats.total_events} />
        <StatCard label="Active Zones" value={stats.live.active_zones} />
        <StatCard label="Aircraft Affected" value={stats.total_aircraft_affected} />
        <div className="flex flex-col items-center px-4">
          <span className="text-xs text-text-primary">
            {stats.date_range.start} — {stats.date_range.end}
          </span>
          <span className="text-[10px] text-text-muted uppercase tracking-wider">Analysis Period</span>
        </div>
      </div>

      <LivePulse
        status={stats.live.poll_status}
        lastPoll={stats.live.last_poll}
      />
    </div>
  );
}
