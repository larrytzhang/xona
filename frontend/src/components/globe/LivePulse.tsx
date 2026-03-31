"use client";

import { clsx } from "clsx";

/**
 * Live polling status indicator.
 *
 * Small pulsing dot with "Live" text and last poll timestamp.
 * Green = active, yellow = delayed, red = disconnected.
 *
 * @param status - Polling status string ('active', 'error', 'inactive').
 * @param lastPoll - ISO timestamp of last successful poll, or null.
 * @returns The live pulse indicator element.
 */
export function LivePulse({
  status = "inactive",
  lastPoll,
}: {
  status?: string;
  lastPoll?: string | null;
}) {
  const color =
    status === "active"
      ? "bg-severity-low"
      : status === "error"
        ? "bg-severity-critical"
        : "bg-severity-moderate";

  const label = status === "active" ? "Live" : status === "error" ? "Error" : "Idle";

  return (
    <div className="flex items-center gap-1.5">
      <div className="relative">
        <div className={clsx("w-2 h-2 rounded-full", color)} />
        {status === "active" && (
          <div
            className={clsx(
              "absolute inset-0 w-2 h-2 rounded-full animate-ping",
              color,
              "opacity-75"
            )}
          />
        )}
      </div>
      <span className="text-xs text-text-secondary">{label}</span>
      {lastPoll && (
        <span className="text-[10px] text-text-muted font-mono-numbers">
          {new Date(lastPoll).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}
