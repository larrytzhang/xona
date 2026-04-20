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
      className="glass rounded-xl p-6 opacity-0 animate-fade-in-up transition-all duration-300 hover:border-accent-cyan/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.08)]"
      style={{ animationDelay: `${index * 120}ms`, animationFillMode: "forwards" }}
    >
      <div className="text-3xl font-bold font-mono-numbers text-accent-cyan mb-2 tracking-tight">
        {finding.value}
      </div>
      <h3 className="text-lg font-semibold mb-1 leading-snug">{finding.title}</h3>
      {finding.detail && (
        <p className="text-sm text-text-secondary leading-relaxed">{finding.detail}</p>
      )}
    </div>
  );
}
