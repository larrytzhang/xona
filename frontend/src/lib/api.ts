/**
 * GPS Shield — Typed API client.
 *
 * Provides typed fetch wrappers for all backend API endpoints.
 * Uses NEXT_PUBLIC_API_URL for the backend base URL, defaulting
 * to localhost:8000 for local development.
 */

import type {
  FindingsResponse,
  HealthResponse,
  RegionsResponse,
  StatsResponse,
  ZoneDetailResponse,
  ZonesHistoryResponse,
  ZonesLiveResponse,
} from "./types";

/** Backend API base URL from environment or localhost default. */
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Typed fetch helper that throws on non-OK responses.
 *
 * @param path - API path (e.g., '/api/stats').
 * @param params - Optional query parameters.
 * @returns Parsed JSON response of type T.
 * @throws Error on non-OK HTTP response.
 */
async function fetchAPI<T>(
  path: string,
  params?: Record<string, string | number>
): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, String(value));
    });
  }

  const res = await fetch(url.toString(), {
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

/**
 * Fetch currently active interference zones.
 *
 * @param hoursBack - How many hours back to look (default 24).
 * @returns ZonesLiveResponse with active zones.
 */
export function fetchZonesLive(hoursBack = 24): Promise<ZonesLiveResponse> {
  return fetchAPI<ZonesLiveResponse>("/api/zones/live", {
    hours_back: hoursBack,
  });
}

/**
 * Fetch historical zones with filters and pagination.
 *
 * @param params - Query parameters for filtering.
 * @returns ZonesHistoryResponse with paginated zone data.
 */
export function fetchZonesHistory(params: {
  start_date: string;
  end_date: string;
  region?: string;
  event_type?: string;
  min_severity?: number;
  page?: number;
  page_size?: number;
}): Promise<ZonesHistoryResponse> {
  return fetchAPI<ZonesHistoryResponse>(
    "/api/zones/history",
    params as Record<string, string | number>
  );
}

/**
 * Fetch detailed view of a single zone with events.
 *
 * @param zoneId - Primary key of the zone.
 * @returns ZoneDetailResponse with zone and event data.
 */
export function fetchZoneDetail(zoneId: number): Promise<ZoneDetailResponse> {
  return fetchAPI<ZoneDetailResponse>(`/api/zones/${zoneId}`);
}

/**
 * Fetch global dashboard statistics.
 *
 * @returns StatsResponse with aggregate counts and live status.
 */
export function fetchStats(): Promise<StatsResponse> {
  return fetchAPI<StatsResponse>("/api/stats");
}

/**
 * Fetch pre-computed key findings.
 *
 * @returns FindingsResponse with 5 headline findings.
 */
export function fetchFindings(): Promise<FindingsResponse> {
  return fetchAPI<FindingsResponse>("/api/findings");
}

/**
 * Fetch per-region breakdown with trend data.
 *
 * @param period - Aggregation period ('daily', 'weekly', 'monthly').
 * @returns RegionsResponse with region breakdowns.
 */
export function fetchRegions(
  period: string = "monthly"
): Promise<RegionsResponse> {
  return fetchAPI<RegionsResponse>("/api/regions", { period });
}

/**
 * Fetch system health status.
 *
 * @returns HealthResponse with database and polling status.
 */
export function fetchHealth(): Promise<HealthResponse> {
  return fetchAPI<HealthResponse>("/health");
}
