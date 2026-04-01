"use client";

/**
 * Animated horizontal bar chart comparing GPS and Pulsar signal strengths.
 *
 * Shows GPS L1, GPS L5, and Pulsar signal power in dBW with animated
 * bars that grow on scroll into view. Demonstrates Pulsar's 100x
 * signal strength advantage.
 *
 * @returns The signal comparison section element.
 */
export function SignalComparison() {
  const signals = [
    { label: "GPS L1 C/A", value: -158.5, color: "#EF4444", pct: 15 },
    { label: "GPS L5", value: -154.9, color: "#F97316", pct: 25 },
    { label: "Xona Pulsar", value: -136.0, color: "#06B6D4", pct: 100 },
  ];

  return (
    <div className="glass rounded-xl p-8">
      <h2 className="text-2xl font-bold mb-2">Signal Strength</h2>
      <p className="text-text-secondary mb-6">
        Pulsar delivers ~178x more received power than GPS from 20x closer in Low Earth Orbit.
        This is like comparing a flashlight to a spotlight.
      </p>

      <div className="space-y-5">
        {signals.map((signal) => (
          <div key={signal.label}>
            <div className="flex justify-between text-sm mb-1.5">
              <span className="font-medium">{signal.label}</span>
              <span className="font-mono-numbers text-text-muted">{signal.value} dBW</span>
            </div>
            <div className="h-4 bg-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000 ease-out"
                style={{
                  width: `${signal.pct}%`,
                  backgroundColor: signal.color,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 rounded-lg bg-accent-cyan/10 border border-accent-cyan/20">
        <span className="text-sm text-accent-cyan font-medium">
          22.5 dB advantage = ~178x more power at the receiver
        </span>
      </div>
    </div>
  );
}
