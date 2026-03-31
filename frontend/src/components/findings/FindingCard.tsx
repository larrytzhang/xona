"use client";

import type { Finding } from "@/lib/types";

/**
 * A single headline finding card with large value and detail text.
 *
 * Displays a key statistic prominently with its title and
 * explanatory detail text below.
 *
 * @param finding - The finding data to display.
 * @param index - Card index for staggered animation delay.
 * @returns A styled finding card element.
 */
export function FindingCard({ finding, index }: { finding: Finding; index: number }) {
  return (
    <div
      className="glass rounded-xl p-6 opacity-0 animate-fade-in-up"
      style={{ animationDelay: `${index * 150}ms`, animationFillMode: "forwards" }}
    >
      <div className="text-3xl font-bold font-mono-numbers text-accent-cyan mb-2">
        {finding.value}
      </div>
      <h3 className="text-lg font-semibold mb-1">{finding.title}</h3>
      {finding.detail && (
        <p className="text-sm text-text-secondary leading-relaxed">{finding.detail}</p>
      )}
    </div>
  );
}
