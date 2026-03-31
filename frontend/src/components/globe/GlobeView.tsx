"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import DeckGL from "@deck.gl/react";
import { _GlobeView as DeckGlobeView } from "@deck.gl/core";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import { ANIMATION, DEFAULT_VIEW_STATE } from "@/lib/constants";
import type { InterferenceZone } from "@/lib/types";

/**
 * Props for the GlobeView component.
 *
 * @param zones - Array of interference zones to render on the globe.
 * @param pulsarMode - Whether Pulsar Mode is active.
 * @param onZoneClick - Callback when a zone is clicked.
 * @param onZoneHover - Callback when a zone is hovered.
 * @param flyTo - Optional lat/lon/zoom to fly the camera to.
 */
interface GlobeViewProps {
  zones?: InterferenceZone[];
  pulsarMode?: boolean;
  onZoneClick?: (zone: InterferenceZone) => void;
  onZoneHover?: (zone: InterferenceZone | null) => void;
  flyTo?: { latitude: number; longitude: number; zoom: number } | null;
}

/**
 * Interactive 3D globe using deck.gl with GlobeView projection.
 *
 * Features:
 *   - Dark Carto basemap tiles.
 *   - Auto-rotation at 0.3 deg/s, pauses on interaction, resumes after 8s.
 *   - Intro animation: fade from black, zoom out to global view.
 *   - Atmospheric glow effect via CSS gradient.
 *   - Accepts zones, pulsarMode, and callbacks for data layer rendering.
 *
 * Data layers (zones, tooltips, etc.) will be added in Step 18.
 *
 * @param props - GlobeViewProps
 * @returns The deck.gl globe component filling its container.
 */
export function GlobeView({
  zones: _zones = [],
  pulsarMode: _pulsarMode = false,
  onZoneClick: _onZoneClick,
  onZoneHover: _onZoneHover,
  flyTo,
}: GlobeViewProps) {
  // Unused props will be wired in Steps 18-19 when data layers are added.
  void _zones;
  void _pulsarMode;
  void _onZoneClick;
  void _onZoneHover;
  const [viewState, setViewState] = useState({
    ...DEFAULT_VIEW_STATE,
    zoom: 2.5, // Start slightly zoomed in for intro animation.
  });
  const [isVisible, setIsVisible] = useState(false);
  const [isInteracting, setIsInteracting] = useState(false);
  const interactionTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const animationFrame = useRef<number | null>(null);

  // Intro animation: fade in and zoom out to default view.
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

  // Auto-rotation loop.
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

  // Handle fly-to requests from external components (region click, etc.).
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

  // Pause auto-rotation on user interaction.
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

  const handleViewStateChange = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ({ viewState: newViewState }: { viewState: any }) => {
      setViewState((prev) => ({ ...prev, ...newViewState }));
    },
    []
  );

  // Dark basemap tile layer (Carto dark-matter-nolabels).
  const basemapLayer = useMemo(
    () =>
      new TileLayer({
        id: "basemap",
        data: "https://basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
        minZoom: 0,
        maxZoom: 6,
        tileSize: 256,
        renderSubLayers: (props: Record<string, unknown>) => {
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

  const views = useMemo(() => new DeckGlobeView({ id: "globe" }), []);

  return (
    <div className="absolute inset-0 pt-14">
      {/* Atmospheric glow effect */}
      <div
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.03) 0%, transparent 60%)",
        }}
      />

      {/* Globe container with intro fade */}
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
          layers={[basemapLayer]}
          getCursor={() => "grab"}
        />
      </div>
    </div>
  );
}
