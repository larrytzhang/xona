"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import DeckGL from "@deck.gl/react";
import { _GlobeView as DeckGlobeView } from "@deck.gl/core";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer, ScatterplotLayer } from "@deck.gl/layers";
import {
  ANIMATION,
  DEFAULT_VIEW_STATE,
  PULSAR_RGBA,
  SEVERITY_RGBA,
  severityLabel,
} from "@/lib/constants";
import type { InterferenceZone } from "@/lib/types";
import { ZoneTooltip } from "./ZoneTooltip";

/**
 * Props for the GlobeView component.
 *
 * @param zones - Array of interference zones to render on the globe.
 * @param pulsarMode - Whether Pulsar Mode is active (shrinks zone radii).
 * @param onZoneClick - Callback when a zone is clicked.
 * @param flyTo - Optional lat/lon/zoom to fly the camera to.
 */
interface GlobeViewProps {
  zones?: InterferenceZone[];
  pulsarMode?: boolean;
  onZoneClick?: (zone: InterferenceZone) => void;
  flyTo?: { latitude: number; longitude: number; zoom: number } | null;
}

/**
 * Interactive 3D globe using deck.gl with GlobeView projection.
 *
 * Renders interference zones as colored circles with radius proportional
 * to the zone's effective area. In Pulsar Mode, radii shrink to show
 * the 6.3x reduction. Live zones pulse with a cyan indicator.
 *
 * @param props - GlobeViewProps
 * @returns The deck.gl globe component with all data layers.
 */
export function GlobeView({
  zones = [],
  pulsarMode = false,
  onZoneClick,
  flyTo,
}: GlobeViewProps) {
  const [viewState, setViewState] = useState({
    ...DEFAULT_VIEW_STATE,
    zoom: 2.5,
  });
  const [isVisible, setIsVisible] = useState(false);
  const [isInteracting, setIsInteracting] = useState(false);
  const [hoveredZone, setHoveredZone] = useState<InterferenceZone | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const interactionTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const animationFrame = useRef<number | null>(null);

  // Intro animation.
  useEffect(() => {
    const fadeTimer = setTimeout(() => setIsVisible(true), 100);
    const zoomTimer = setTimeout(() => {
      setViewState((prev) => ({
        ...prev,
        zoom: DEFAULT_VIEW_STATE.zoom,
        transitionDuration: 1500,
      }));
    }, ANIMATION.INTRO_FADE_MS);
    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(zoomTimer);
    };
  }, []);

  // Auto-rotation.
  useEffect(() => {
    if (isInteracting) {
      if (animationFrame.current) cancelAnimationFrame(animationFrame.current);
      return;
    }
    let lastTime = performance.now();
    const rotate = (now: number) => {
      const dt = (now - lastTime) / 1000;
      lastTime = now;
      setViewState((prev) => ({
        ...prev,
        longitude: prev.longitude + ANIMATION.ROTATION_SPEED * dt,
      }));
      animationFrame.current = requestAnimationFrame(rotate);
    };
    animationFrame.current = requestAnimationFrame(rotate);
    return () => {
      if (animationFrame.current) cancelAnimationFrame(animationFrame.current);
    };
  }, [isInteracting]);

  // Fly-to from external triggers.
  useEffect(() => {
    if (flyTo) {
      setViewState((prev) => ({
        ...prev,
        latitude: flyTo.latitude,
        longitude: flyTo.longitude,
        zoom: flyTo.zoom,
        transitionDuration: ANIMATION.FLY_TO_MS,
      }));
    }
  }, [flyTo]);

  const handleInteractionStart = useCallback(() => {
    setIsInteracting(true);
    if (interactionTimer.current) clearTimeout(interactionTimer.current);
  }, []);

  const handleInteractionEnd = useCallback(() => {
    if (interactionTimer.current) clearTimeout(interactionTimer.current);
    interactionTimer.current = setTimeout(() => {
      setIsInteracting(false);
    }, ANIMATION.IDLE_TIMEOUT_MS);
  }, []);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleViewStateChange = useCallback(({ viewState: vs }: { viewState: any }) => {
    setViewState((prev) => ({ ...prev, ...vs }));
  }, []);

  // --- Data layers ---

  /** Zone circles: color by severity, radius = interference area. */
  const zoneLayer = useMemo(
    () =>
      new ScatterplotLayer<InterferenceZone>({
        id: "zones",
        data: zones,
        pickable: true,
        stroked: true,
        filled: true,
        radiusUnits: "meters",
        lineWidthMinPixels: 1,
        getPosition: (d) => [d.center_lon, d.center_lat],
        getRadius: (d) => {
          const km = pulsarMode
            ? (d.pulsar_jam_radius_km ?? d.radius_km / 6.3)
            : d.radius_km;
          return km * 1000;
        },
        getFillColor: (d) => {
          if (pulsarMode) return [...PULSAR_RGBA.slice(0, 3), 60] as [number, number, number, number];
          const label = severityLabel(d.severity);
          const rgba = SEVERITY_RGBA[label] || SEVERITY_RGBA.moderate;
          return [rgba[0], rgba[1], rgba[2], 80];
        },
        getLineColor: (d) => {
          if (pulsarMode) return PULSAR_RGBA;
          const label = severityLabel(d.severity);
          return SEVERITY_RGBA[label] || SEVERITY_RGBA.moderate;
        },
        getLineWidth: 2,
        transitions: {
          getRadius: { duration: ANIMATION.PULSAR_TRANSITION_MS, easing: easeInOutCubic },
          getFillColor: { duration: ANIMATION.PULSAR_TRANSITION_MS },
          getLineColor: { duration: ANIMATION.PULSAR_TRANSITION_MS },
        },
        onClick: (info) => {
          if (info.object && onZoneClick) {
            onZoneClick(info.object);
          }
        },
        onHover: (info) => {
          setHoveredZone(info.object || null);
          setTooltipPos({ x: info.x ?? 0, y: info.y ?? 0 });
        },
        updateTriggers: {
          getRadius: pulsarMode,
          getFillColor: pulsarMode,
          getLineColor: pulsarMode,
        },
      }),
    [zones, pulsarMode, onZoneClick]
  );

  /** Live pulse dots: small cyan pulsing circles for is_live zones. */
  const livePulseLayer = useMemo(
    () =>
      new ScatterplotLayer<InterferenceZone>({
        id: "live-pulse",
        data: zones.filter((z) => z.is_live),
        pickable: false,
        filled: true,
        radiusUnits: "meters",
        getPosition: (d) => [d.center_lon, d.center_lat],
        getRadius: 15000,
        getFillColor: [6, 182, 212, 180],
      }),
    [zones]
  );

  /** Pulsar shield glow: larger faint cyan circles in Pulsar Mode. */
  const shieldLayer = useMemo(
    () =>
      pulsarMode
        ? new ScatterplotLayer<InterferenceZone>({
            id: "pulsar-shield",
            data: zones,
            pickable: false,
            filled: true,
            radiusUnits: "meters",
            getPosition: (d) => [d.center_lon, d.center_lat],
            getRadius: (d) => (d.pulsar_jam_radius_km ?? d.radius_km / 6.3) * 1000 * 1.5,
            getFillColor: [6, 182, 212, 25],
          })
        : null,
    [zones, pulsarMode]
  );

  // Basemap tiles.
  const basemapLayer = useMemo(
    () =>
      new TileLayer({
        id: "basemap",
        data: "https://basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
        minZoom: 0,
        maxZoom: 6,
        tileSize: 256,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        renderSubLayers: (props: any) => {
          const { boundingBox } = props.tile as {
            boundingBox: [[number, number], [number, number]];
          };
          return new BitmapLayer({
            ...props,
            data: undefined,
            image: props.data as string,
            bounds: [
              boundingBox[0][0],
              boundingBox[0][1],
              boundingBox[1][0],
              boundingBox[1][1],
            ],
          });
        },
      }),
    []
  );

  const layers = useMemo(() => {
    const result = [basemapLayer, zoneLayer, livePulseLayer];
    if (shieldLayer) result.push(shieldLayer);
    return result;
  }, [basemapLayer, zoneLayer, livePulseLayer, shieldLayer]);

  const views = useMemo(() => new DeckGlobeView({ id: "globe" }), []);

  return (
    <div className="absolute inset-0 pt-14">
      {/* Atmospheric glow */}
      <div
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.03) 0%, transparent 60%)",
        }}
      />

      {/* Globe with intro fade */}
      <div
        className="w-full h-full transition-opacity duration-700"
        style={{ opacity: isVisible ? 1 : 0 }}
      >
        <DeckGL
          views={views}
          viewState={viewState}
          onViewStateChange={handleViewStateChange}
          controller={{
            inertia: true,
            scrollZoom: { speed: 0.01, smooth: true },
          }}
          onDragStart={handleInteractionStart}
          onDragEnd={handleInteractionEnd}
          layers={layers}
          getCursor={({ isHovering }) => (isHovering ? "pointer" : "grab")}
        />
      </div>

      {/* Hover tooltip */}
      <ZoneTooltip zone={hoveredZone} x={tooltipPos.x} y={tooltipPos.y} />
    </div>
  );
}

/** Cubic ease-in-out for smooth Pulsar toggle transitions. */
function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
