"use client";

import type { RegionData } from "@/lib/types";

/**
 * Events over time area chart using pure SVG.
 *
 * Shows a stacked bar chart of events per month across regions.
 * Uses inline SVG rather than Recharts for build simplicity.
 *
 * @param regions - Array of region data with trend series.
 * @returns An SVG area chart element.
 */
export function TrendChart({ regions }: { regions: RegionData[] }) {
  if (!regions.length) return null;

  // Collect all unique periods.
  const allPeriods = new Set<string>();
  regions.forEach((r) => r.trend.forEach((t) => allPeriods.add(t.period)));
  const periods = Array.from(allPeriods).sort();

  if (periods.length < 2) return null;

  // Build stacked data.
  const stacked: number[][] = periods.map((period) => {
    return regions.map((r) => {
      const point = r.trend.find((t) => t.period === period);
      return point?.events ?? 0;
    });
  });

  const totals = stacked.map((s) => s.reduce((a, b) => a + b, 0));
  const maxTotal = Math.max(...totals, 1);

  const width = 600;
  const height = 200;
  const padding = { top: 20, right: 20, bottom: 30, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const colors = ["#06B6D4", "#3B82F6", "#8B5CF6", "#F59E0B", "#EF4444", "#10B981", "#EC4899"];

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-sm font-medium text-text-secondary mb-3">Events Over Time by Region</h3>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label="Stacked bar chart showing GPS interference events over time by region">
        {/* Y-axis labels */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const y = padding.top + chartH * (1 - frac);
          const val = Math.round(maxTotal * frac);
          return (
            <g key={frac}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#27272A"
                strokeWidth={0.5}
              />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fill="#71717A" fontSize={9}>
                {val.toLocaleString()}
              </text>
            </g>
          );
        })}

        {/* Stacked bars */}
        {periods.map((period, i) => {
          const x = padding.left + (i / (periods.length - 1)) * chartW;
          let cumY = 0;
          return (
            <g key={period}>
              {stacked[i].map((val, ri) => {
                const barH = (val / maxTotal) * chartH;
                const y = padding.top + chartH - cumY - barH;
                cumY += barH;
                return (
                  <rect
                    key={ri}
                    x={x - chartW / periods.length / 2.5}
                    y={y}
                    width={chartW / periods.length / 1.5}
                    height={Math.max(barH, 0)}
                    fill={colors[ri % colors.length]}
                    opacity={0.8}
                    rx={2}
                  />
                );
              })}
              {/* X-axis label */}
              <text
                x={x}
                y={height - 8}
                textAnchor="middle"
                fill="#71717A"
                fontSize={9}
              >
                {period}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-2">
        {regions.map((r, i) => (
          <div key={r.region} className="flex items-center gap-1">
            <div
              className="w-2.5 h-2.5 rounded-sm"
              style={{ backgroundColor: colors[i % colors.length] }}
            />
            <span className="text-[10px] text-text-muted">{r.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
