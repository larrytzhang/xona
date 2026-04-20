"use client";

import { useEffect, useState } from "react";

/**
 * Animated horizontal bar chart comparing GPS and Pulsar signal strengths.
 *
 * Shows GPS L1, GPS L5, and Pulsar signal power in dBW with bars that
 * grow from 0 on mount. Demonstrates Pulsar's ~178x signal advantage.
 */
export function SignalComparison() {
  const signals = [
    { label: "GPS L1 C/A", value: -158.5, color: "#EF4444", pct: 15 },
    { label: "GPS L5", value: -154.9, color: "#F97316", pct: 25 },
    { label: "Xona Pulsar", value: -136.0, color: "#06B6D4", pct: 100 },
  ];

  // Trigger CSS transition by mounting with width: 0 and then updating.
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <div className="glass rounded-xl p-6 md:p-8">
      <h2 className="text-2xl font-bold mb-2">Signal Strength</h2>
      <p className="text-text-secondary mb-6 leading-relaxed">
        Pulsar delivers ~178x more received power than GPS from 20x closer in
        Low Earth Orbit. Like comparing a flashlight to a spotlight.
      </p>

      <div className="space-y-5">
        {signals.map((signal, i) => (
          <div key={signal.label}>
            <div className="flex justify-between text-sm mb-1.5">
              <span className="font-medium">{signal.label}</span>
              <span className="font-mono-numbers text-text-muted">{signal.value} dBW</span>
            </div>
            <div className="h-4 bg-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-[width] duration-1000 ease-out"
                style={{
                  width: `${mounted ? signal.pct : 0}%`,
                  backgroundColor: signal.color,
                  transitionDelay: `${i * 120}ms`,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 p-3 rounded-lg bg-accent-cyan/10 border border-accent-cyan/20">
        <span className="text-sm text-accent-cyan font-medium">
          22.5 dB advantage = ~178x more power at the receiver
        </span>
      </div>
    </div>
  );
}
