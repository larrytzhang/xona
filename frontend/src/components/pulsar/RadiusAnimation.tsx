"use client";

/**
 * Animated SVG comparing GPS vs Pulsar jamming radii.
 *
 * Two concentric circles: outer red (GPS radius) and inner cyan (Pulsar).
 * Visually demonstrates the 97% area reduction — the Pulsar circle is
 * dramatically smaller than the GPS circle.
 *
 * @returns The radius comparison SVG element.
 */
export function RadiusAnimation() {
  const gpsRadius = 150; // km (example)
  const pulsarRadius = 23.8; // km (150 / 6.3)
  const svgSize = 300;
  const center = svgSize / 2;
  const scale = 0.9; // fraction of SVG radius to use
  const gpsR = (svgSize / 2) * scale;
  const pulsarR = gpsR * (pulsarRadius / gpsRadius);

  return (
    <div className="glass rounded-xl p-8">
      <h2 className="text-2xl font-bold mb-2">Jamming Radius Reduction</h2>
      <p className="text-text-secondary mb-6">
        A jammer that affects a 150 km radius with GPS would only affect 24 km
        with Pulsar — 97.5% less area.
      </p>

      <div className="flex justify-center mb-6">
        <svg width={svgSize} height={svgSize} viewBox={`0 0 ${svgSize} ${svgSize}`}>
          {/* GPS radius (outer, red) */}
          <circle
            cx={center}
            cy={center}
            r={gpsR}
            fill="rgba(239, 68, 68, 0.1)"
            stroke="#EF4444"
            strokeWidth={2}
            strokeDasharray="4 4"
          />
          <text
            x={center}
            y={center - gpsR - 8}
            textAnchor="middle"
            fill="#EF4444"
            fontSize={11}
            fontFamily="JetBrains Mono, monospace"
          >
            GPS: {gpsRadius} km
          </text>

          {/* Pulsar radius (inner, cyan) */}
          <circle
            cx={center}
            cy={center}
            r={pulsarR}
            fill="rgba(6, 182, 212, 0.2)"
            stroke="#06B6D4"
            strokeWidth={2}
          />

          {/* Pulsar label */}
          <text
            x={center}
            y={center + 4}
            textAnchor="middle"
            fill="#06B6D4"
            fontSize={10}
            fontFamily="JetBrains Mono, monospace"
          >
            Pulsar
          </text>
          <text
            x={center}
            y={center + 16}
            textAnchor="middle"
            fill="#06B6D4"
            fontSize={10}
            fontFamily="JetBrains Mono, monospace"
          >
            {pulsarRadius} km
          </text>

          {/* Area label */}
          <text
            x={center}
            y={svgSize - 10}
            textAnchor="middle"
            fill="#71717A"
            fontSize={10}
          >
            97.5% area reduction
          </text>
        </svg>
      </div>

      <div className="p-3 rounded-lg bg-bg-elevated text-sm text-text-secondary">
        Jammer effective radius scales as the square root of the signal power ratio.
        Pulsar&apos;s 6.3x radius reduction means only 2.5% of the GPS-vulnerable area
        remains affected.
      </div>
    </div>
  );
}
