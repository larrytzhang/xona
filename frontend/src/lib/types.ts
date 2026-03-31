/**
 * GPS Shield — TypeScript type definitions.
 *
 * All types mirror the Pydantic response schemas in the backend's
 * schemas.py exactly. Frontend code must use these types for all
 * API responses — no `any` types allowed.
 */

/** A single interference zone as returned by the API. */
export interface InterferenceZone {
  id: number;
  center_lat: number;
  center_lon: number;
  radius_km: number;
  event_type: "spoofing" | "jamming" | "mixed";
  severity: number;
  affected_aircraft: number;
  start_time: string;
  end_time: string | null;
  status: "active" | "resolved";
  region: string;
  is_live: boolean;
  gps_jam_radius_km: number | null;
  pulsar_jam_radius_km: number | null;
  spoofing_eliminated: boolean;
  signal_advantage_db: number | null;
  area_reduction_pct: number | null;
}

/** Response for GET /api/zones/live. */
export interface ZonesLiveResponse {
  count: number;
  last_poll: string | null;
  poll_status: string;
  zones: InterferenceZone[];
}

/** Response for GET /api/zones/history. */
export interface ZonesHistoryResponse {
  total_count: number;
  page: number;
  page_size: number;
  zones: InterferenceZone[];
}

/** A single detector flag from an anomaly event. */
export interface AnomalyFlag {
  detector: string;
  value: number;
  threshold: number;
  confidence: number;
  detail: string;
}

/** A single anomaly event (aircraft detection). */
export interface AnomalyEvent {
  id: number;
  ts: string;
  icao24: string;
  callsign: string | null;
  latitude: number;
  longitude: number;
  altitude_m: number | null;
  anomaly_type: "spoofing" | "jamming" | "anomaly";
  severity: number;
  severity_label: "low" | "moderate" | "elevated" | "high" | "critical";
  flags: AnomalyFlag[];
}

/** Response for GET /api/zones/{zone_id}. */
export interface ZoneDetailResponse {
  zone: InterferenceZone;
  events: AnomalyEvent[];
}

/** Date range for analysis period. */
export interface DateRange {
  start: string;
  end: string;
}

/** Event counts by type. */
export interface ByType {
  spoofing: number;
  jamming: number;
  mixed: number;
}

/** Live polling status. */
export interface LiveStats {
  active_zones: number;
  events_last_hour: number;
  last_poll: string | null;
  poll_status: string;
}

/** Response for GET /api/stats. */
export interface StatsResponse {
  total_events: number;
  total_zones: number;
  total_aircraft_affected: number;
  date_range: DateRange;
  by_type: ByType;
  avg_severity: number;
  live: LiveStats;
}

/** A single pre-computed key finding. */
export interface Finding {
  finding_key: string;
  title: string;
  value: string;
  detail: string | null;
}

/** Response for GET /api/findings. */
export interface FindingsResponse {
  findings: Finding[];
  computed_at: string | null;
}

/** A data point in a region's trend series. */
export interface TrendPoint {
  period: string;
  events: number;
}

/** Per-region data with trend. */
export interface RegionData {
  region: string;
  name: string;
  total_events: number;
  spoofing_events: number;
  jamming_events: number;
  unique_aircraft: number;
  avg_severity: number;
  trend: TrendPoint[];
}

/** Response for GET /api/regions. */
export interface RegionsResponse {
  regions: RegionData[];
}

/** Response for GET /health. */
export interface HealthResponse {
  status: string;
  database: string;
  live_polling: string;
  last_poll: string | null;
  version: string;
}
