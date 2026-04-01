"use client";

/**
 * GPS Shield — React Query hooks for API data fetching.
 *
 * Wraps each API endpoint in a typed useQuery hook with appropriate
 * staleTime for each data type:
 *   - zones/live: 15 seconds (frequently updated by polling).
 *   - stats: 30 seconds.
 *   - findings: 5 minutes (rarely changes).
 *   - regions: 1 minute.
 *   - zone detail: 30 seconds.
 */

import { useQuery } from "@tanstack/react-query";
import {
  fetchFindings,
  fetchRegions,
  fetchStats,
  fetchZoneDetail,
  fetchZonesHistory,
  fetchZonesLive,
} from "./api";
import type {
  FindingsResponse,
  RegionsResponse,
  StatsResponse,
  ZoneDetailResponse,
  ZonesHistoryResponse,
  ZonesLiveResponse,
} from "./types";

/**
 * Fetch active interference zones with automatic refetching.
 *
 * @param hoursBack - How many hours back to look (default 24).
 * @returns React Query result with ZonesLiveResponse data.
 */
export function useZonesLive(hoursBack = 24) {
  return useQuery<ZonesLiveResponse>({
    queryKey: ["zones", "live", hoursBack],
    queryFn: () => fetchZonesLive(hoursBack),
    staleTime: 15 * 1000,
    refetchInterval: 15 * 1000,
  });
}

/**
 * Fetch historical zones with filters.
 *
 * @param params - Query parameters for filtering.
 * @returns React Query result with ZonesHistoryResponse data.
 */
export function useZonesHistory(params: {
  start_date: string;
  end_date: string;
  region?: string;
  event_type?: string;
  min_severity?: number;
  page?: number;
  page_size?: number;
}) {
  return useQuery<ZonesHistoryResponse>({
    queryKey: ["zones", "history", params],
    queryFn: () => fetchZonesHistory(params),
    staleTime: 60 * 1000,
  });
}

/**
 * Fetch detailed zone data with events.
 *
 * @param zoneId - Zone primary key, or null to skip.
 * @returns React Query result with ZoneDetailResponse data.
 */
export function useZoneDetail(zoneId: number | null) {
  return useQuery<ZoneDetailResponse>({
    queryKey: ["zones", "detail", zoneId],
    queryFn: () => fetchZoneDetail(zoneId!),
    enabled: zoneId !== null,
    staleTime: 30 * 1000,
  });
}

/**
 * Fetch global dashboard statistics.
 *
 * @returns React Query result with StatsResponse data.
 */
export function useStats() {
  return useQuery<StatsResponse>({
    queryKey: ["stats"],
    queryFn: fetchStats,
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  });
}

/**
 * Fetch pre-computed key findings.
 *
 * @returns React Query result with FindingsResponse data.
 */
export function useFindings() {
  return useQuery<FindingsResponse>({
    queryKey: ["findings"],
    queryFn: fetchFindings,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Fetch per-region breakdowns with trends.
 *
 * @param period - Aggregation period (default 'monthly').
 * @returns React Query result with RegionsResponse data.
 */
export function useRegions(period: string = "monthly") {
  return useQuery<RegionsResponse>({
    queryKey: ["regions", period],
    queryFn: () => fetchRegions(period),
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000,
  });
}
