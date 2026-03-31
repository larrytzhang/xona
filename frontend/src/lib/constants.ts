/**
 * GPS Shield — Shared constants.
 *
 * Color maps, severity labels, region metadata, and map defaults
 * used across all frontend components.
 */

/** Severity color mapping for zone visualization. */
export const SEVERITY_COLORS: Record<string, string> = {
  low: "#22C55E",
  moderate: "#EAB308",
  elevated: "#F97316",
  high: "#F97316",
  critical: "#EF4444",
};

/** Severity color as [R, G, B, A] for deck.gl layers (0-255). */
export const SEVERITY_RGBA: Record<string, [number, number, number, number]> = {
  low: [34, 197, 94, 200],
  moderate: [234, 179, 8, 200],
  elevated: [249, 115, 22, 200],
  high: [249, 115, 22, 200],
  critical: [239, 68, 68, 200],
};

/**
 * Map a numeric severity score (0-100) to a human-readable label.
 *
 * @param score - Severity score from 0 to 100.
 * @returns One of: 'low', 'moderate', 'elevated', 'high', 'critical'.
 */
export function severityLabel(score: number): string {
  if (score < 20) return "low";
  if (score < 40) return "moderate";
  if (score < 60) return "elevated";
  if (score < 80) return "high";
  return "critical";
}

/**
 * Map a numeric severity score to a hex color string.
 *
 * @param score - Severity score from 0 to 100.
 * @returns Hex color string (e.g., '#EF4444' for critical).
 */
export function severityColor(score: number): string {
  return SEVERITY_COLORS[severityLabel(score)] || "#71717A";
}

/** Human-readable region display names. */
export const REGION_NAMES: Record<string, string> = {
  baltic_sea: "Baltic Sea",
  eastern_med: "Eastern Mediterranean",
  persian_gulf: "Persian Gulf",
  red_sea: "Red Sea",
  black_sea: "Black Sea",
  ukraine_frontline: "Ukraine Frontline",
  south_china_sea: "South China Sea",
  other: "Other",
};

/** Region center coordinates for camera fly-to. */
export const REGION_CENTERS: Record<string, { latitude: number; longitude: number; zoom: number }> = {
  baltic_sea: { latitude: 57.0, longitude: 22.0, zoom: 4 },
  eastern_med: { latitude: 35.0, longitude: 34.0, zoom: 4.5 },
  persian_gulf: { latitude: 26.5, longitude: 54.0, zoom: 4.5 },
  red_sea: { latitude: 15.0, longitude: 42.0, zoom: 4 },
  black_sea: { latitude: 43.0, longitude: 35.0, zoom: 4.5 },
  ukraine_frontline: { latitude: 49.0, longitude: 36.0, zoom: 5 },
  south_china_sea: { latitude: 15.0, longitude: 115.0, zoom: 4 },
};

/** Default globe view state (centered on Middle East). */
export const DEFAULT_VIEW_STATE = {
  latitude: 25,
  longitude: 35,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
};

/** Pulsar-mode accent color (cyan). */
export const PULSAR_COLOR = "#06B6D4";
export const PULSAR_RGBA: [number, number, number, number] = [6, 182, 212, 200];

/** Animation timing constants. */
export const ANIMATION = {
  /** Pulsar toggle radius shrink duration (ms). */
  PULSAR_TRANSITION_MS: 1500,
  /** Intro fade-in duration (ms). */
  INTRO_FADE_MS: 600,
  /** Camera fly-to duration (ms). */
  FLY_TO_MS: 2000,
  /** Auto-rotation speed (degrees per second). */
  ROTATION_SPEED: 0.3,
  /** Idle timeout before auto-rotation resumes (ms). */
  IDLE_TIMEOUT_MS: 8000,
};
