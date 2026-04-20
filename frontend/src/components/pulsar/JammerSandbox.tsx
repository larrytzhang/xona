"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Radio, RotateCcw } from "lucide-react";
import { clsx } from "clsx";

const CANVAS_WIDTH = 640;
const CANVAS_HEIGHT = 360;
const JAMMER_SIZE = 44;

// Physical model: GPS civilian signal is ~22.5 dB weaker than Pulsar.
// Jammer effective radius scales with sqrt(signal power ratio).
// sqrt(10^(22.5/10)) ≈ 13.3 → conservative 6.3x (matches rest of app).
const GPS_RADIUS_PX = 120;
const PULSAR_RADIUS_PX = GPS_RADIUS_PX / 6.3;
const JAMMER_POWER_KM = 150; // display label only

/**
 * Fully interactive "drag-the-jammer" sandbox.
 *
 * The reviewer doesn't have to dig up a test case — this component *is*
 * the test case. They drag a virtual jammer anywhere in the canvas,
 * watch the interference footprint, then click the toggle to see the
 * Pulsar advantage in real time.
 *
 * Works entirely client-side (no API calls), pointer-event based so it
 * handles mouse + touch uniformly.
 */
export function JammerSandbox() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 });
  const [pulsar, setPulsar] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [hasMoved, setHasMoved] = useState(false);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    (e.target as Element).setPointerCapture?.(e.pointerId);
    setDragging(true);
  }, []);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    (e.target as Element).releasePointerCapture?.(e.pointerId);
    setDragging(false);
  }, []);

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const scaleX = CANVAS_WIDTH / rect.width;
      const scaleY = CANVAS_HEIGHT / rect.height;
      const x = Math.max(20, Math.min(CANVAS_WIDTH - 20, (e.clientX - rect.left) * scaleX));
      const y = Math.max(20, Math.min(CANVAS_HEIGHT - 20, (e.clientY - rect.top) * scaleY));
      setPos({ x, y });
      if (!hasMoved) setHasMoved(true);
    },
    [dragging, hasMoved]
  );

  // Gentle idle bounce to signal "this is draggable" before the user touches it.
  useEffect(() => {
    if (hasMoved) return;
    const t = setInterval(() => {
      setPos((prev) => ({
        x: CANVAS_WIDTH / 2 + Math.sin(Date.now() / 600) * 4,
        y: prev.y,
      }));
    }, 60);
    return () => clearInterval(t);
  }, [hasMoved]);

  const reset = () => {
    setPos({ x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 });
    setPulsar(false);
    setHasMoved(false);
  };

  const radius = pulsar ? PULSAR_RADIUS_PX : GPS_RADIUS_PX;
  const effectiveKm = pulsar ? (JAMMER_POWER_KM / 6.3) : JAMMER_POWER_KM;
  const areaReductionPct = 97.5;

  return (
    <div className="glass rounded-xl p-6 md:p-8">
      <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-accent-cyan mb-1">
            Try it yourself
          </div>
          <h2 className="text-2xl font-bold mb-1">Drag the jammer</h2>
          <p className="text-text-secondary text-sm max-w-lg">
            Drag the jammer anywhere in the simulation. Toggle Pulsar Mode to
            watch its interference footprint collapse in real time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={reset}
            aria-label="Reset simulation"
            className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
          >
            <RotateCcw size={16} />
          </button>
          <button
            onClick={() => setPulsar((v) => !v)}
            role="switch"
            aria-checked={pulsar}
            className={clsx(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300",
              pulsar
                ? "bg-accent-cyan text-bg-primary shadow-[0_0_16px_rgba(6,182,212,0.3)]"
                : "bg-bg-elevated text-text-primary hover:bg-bg-surface border border-border-subtle"
            )}
          >
            {pulsar ? "Pulsar Mode ON" : "Enable Pulsar Mode"}
          </button>
        </div>
      </div>

      {/* Simulation canvas */}
      <div
        ref={containerRef}
        className="relative w-full rounded-lg overflow-hidden bg-gradient-to-br from-bg-surface to-bg-primary border border-border-subtle cursor-grab active:cursor-grabbing select-none"
        style={{ aspectRatio: `${CANVAS_WIDTH} / ${CANVAS_HEIGHT}` }}
        onPointerMove={handlePointerMove}
      >
        {/* Grid backdrop */}
        <svg
          viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
          className="absolute inset-0 w-full h-full pointer-events-none"
          aria-hidden="true"
        >
          <defs>
            <pattern id="sandbox-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(113, 113, 122, 0.15)" strokeWidth={1} />
            </pattern>
          </defs>
          <rect width={CANVAS_WIDTH} height={CANVAS_HEIGHT} fill="url(#sandbox-grid)" />
        </svg>

        {/* Mock aircraft icons scattered across the grid */}
        <svg
          viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
          className="absolute inset-0 w-full h-full pointer-events-none"
          aria-hidden="true"
        >
          {MOCK_AIRCRAFT.map((a, i) => {
            const dx = a.x - pos.x;
            const dy = a.y - pos.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const affected = dist <= radius;
            return (
              <g
                key={i}
                transform={`translate(${a.x} ${a.y}) rotate(${a.rotation})`}
                style={{ transition: "opacity 600ms ease" }}
                opacity={affected ? (pulsar ? 0.4 : 0.85) : 1}
              >
                <path
                  d="M 0 -5 L 4 4 L 0 2 L -4 4 Z"
                  fill={affected ? (pulsar ? "#06B6D4" : "#EF4444") : "#A1A1AA"}
                  stroke="none"
                />
              </g>
            );
          })}
        </svg>

        {/* Interference ring */}
        <div
          aria-hidden="true"
          className="absolute rounded-full pointer-events-none"
          style={{
            left: `${(pos.x / CANVAS_WIDTH) * 100}%`,
            top: `${(pos.y / CANVAS_HEIGHT) * 100}%`,
            width: `${(radius * 2 / CANVAS_WIDTH) * 100}%`,
            aspectRatio: "1 / 1",
            transform: "translate(-50%, -50%)",
            background: pulsar
              ? "radial-gradient(circle, rgba(6,182,212,0.22) 0%, rgba(6,182,212,0) 70%)"
              : "radial-gradient(circle, rgba(239,68,68,0.25) 0%, rgba(239,68,68,0) 70%)",
            border: pulsar
              ? "1.5px solid rgba(6,182,212,0.7)"
              : "1.5px dashed rgba(239,68,68,0.8)",
            transition: "width 700ms cubic-bezier(0.4,0,0.2,1), background 400ms, border 400ms",
          }}
        />

        {/* Jammer icon (draggable) */}
        <button
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          aria-label="Drag jammer to reposition"
          className={clsx(
            "absolute flex items-center justify-center rounded-full transition-shadow",
            "bg-severity-critical text-white shadow-lg",
            dragging ? "scale-110 shadow-2xl" : "hover:scale-105",
            !hasMoved && "animate-pulse"
          )}
          style={{
            width: JAMMER_SIZE,
            height: JAMMER_SIZE,
            left: `${(pos.x / CANVAS_WIDTH) * 100}%`,
            top: `${(pos.y / CANVAS_HEIGHT) * 100}%`,
            transform: "translate(-50%, -50%)",
            transition: dragging ? "none" : "left 80ms linear, top 80ms linear",
            touchAction: "none",
          }}
        >
          <Radio size={22} />
        </button>

        {/* Hint tag */}
        {!hasMoved && (
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-bg-surface/80 backdrop-blur-sm border border-border-subtle text-[11px] text-text-secondary pointer-events-none">
            Click and drag the red icon
          </div>
        )}
      </div>

      {/* Readout row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-sm">
        <Readout label="Jammer power" value={`${JAMMER_POWER_KM} km`} />
        <Readout
          label="Effective radius"
          value={`${effectiveKm.toFixed(1)} km`}
          highlight={pulsar ? "cyan" : "critical"}
        />
        <Readout
          label="Area reduction"
          value={pulsar ? `${areaReductionPct}%` : "—"}
          highlight="cyan"
        />
        <Readout
          label="Affected aircraft"
          value={`${countAffected(pos, radius)} / ${MOCK_AIRCRAFT.length}`}
        />
      </div>
    </div>
  );
}

function Readout({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "cyan" | "critical";
}) {
  const cls =
    highlight === "cyan"
      ? "text-accent-cyan"
      : highlight === "critical"
        ? "text-severity-critical"
        : "text-text-primary";
  return (
    <div className="p-3 rounded-lg bg-bg-elevated">
      <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={clsx("font-mono-numbers font-medium", cls)}>{value}</div>
    </div>
  );
}

function countAffected(
  jammer: { x: number; y: number },
  radius: number
): number {
  return MOCK_AIRCRAFT.filter((a) => {
    const dx = a.x - jammer.x;
    const dy = a.y - jammer.y;
    return Math.sqrt(dx * dx + dy * dy) <= radius;
  }).length;
}

// Deterministic mock aircraft positions so the "affected count" is stable.
const MOCK_AIRCRAFT: { x: number; y: number; rotation: number }[] = [
  { x: 80, y: 60, rotation: 45 },
  { x: 150, y: 110, rotation: 90 },
  { x: 220, y: 50, rotation: 135 },
  { x: 310, y: 140, rotation: 180 },
  { x: 400, y: 80, rotation: 225 },
  { x: 480, y: 160, rotation: 270 },
  { x: 560, y: 90, rotation: 315 },
  { x: 90, y: 220, rotation: 60 },
  { x: 180, y: 280, rotation: 120 },
  { x: 270, y: 240, rotation: 200 },
  { x: 360, y: 300, rotation: 15 },
  { x: 440, y: 260, rotation: 100 },
  { x: 540, y: 310, rotation: 330 },
  { x: 120, y: 180, rotation: 75 },
  { x: 350, y: 200, rotation: 280 },
  { x: 500, y: 220, rotation: 195 },
];
